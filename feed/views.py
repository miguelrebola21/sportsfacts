from io import BytesIO
import random
from urllib.parse import quote, urlencode

from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from PIL import Image, ImageDraw, ImageFont

from .models import Fact, Record, Tag

PIXEL_LETTERS = {
    "s": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "p": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "o": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "r": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "t": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "f": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "a": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "c": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
}


def home(request):
    selected_tag_names = _selected_tag_names(request)
    facts = Fact.objects.select_related("invalidates").prefetch_related("tags")
    records = Record.objects.select_related("invalidates").prefetch_related("tags")
    selected_tags = list(Tag.objects.filter(name__in=selected_tag_names))
    selected_tag_names = [tag.name for tag in selected_tags]
    fact_cards = []
    record_cards = []

    for tag in selected_tags:
        facts = facts.filter(tags=tag)
        records = records.filter(tags=tag)

    for fact in facts:
        fact_cards.append(_card_context(request, "fact", fact, fact.id, f"Fact #{fact.id}", fact.text, selected_tag_names))

    for record in records:
        record_cards.append(_card_context(request, "record", record, record.id, f"Record #{record.number}", record.text, selected_tag_names))

    cards = _interleaved_cards(fact_cards, record_cards)

    return render(
        request,
        "feed/home.html",
        {
            "cards": cards,
            "selected_tags": [
                {"name": tag.name, "remove_url": _tags_url([name for name in selected_tag_names if name != tag.name])}
                for tag in selected_tags
            ],
        },
    )


def vote(request, item_type, item_id, direction):
    if request.method != "POST":
        raise Http404

    model = _model_for_type(item_type)
    field = {"up": "upvotes", "down": "downvotes"}.get(direction)
    if field is None:
        raise Http404

    updated = model.objects.filter(id=item_id).update(**{field: F(field) + 1})
    if not updated:
        raise Http404

    return redirect("feed:home")


def share_image(request, item_type, item_id):
    item = _get_item(item_type, item_id)
    title, body = _display_parts(item_type, item)
    scale = 2
    image = Image.new("RGB", (1200 * scale, 630 * scale), "#002030")
    draw = ImageDraw.Draw(image)

    _draw_pixel_logo(draw, image.width, 54 * scale, scale)
    _draw_share_card(draw, item_type, title, body, scale)

    output = BytesIO()
    image.save(output, format="PNG")
    return HttpResponse(output.getvalue(), content_type="image/png")


def share(request, item_type, item_id):
    item = _get_item(item_type, item_id)
    title, body = _display_parts(item_type, item)
    image_url = request.build_absolute_uri(reverse("feed:share_image", args=[item_type, item_id]))
    page_url = request.build_absolute_uri(reverse("feed:share", args=[item_type, item_id]))

    return render(
        request,
        "feed/share.html",
        {
            "title": title,
            "body": body,
            "image_url": image_url,
            "page_url": page_url,
        },
    )


def _card_context(request, item_type, item, item_id, title, body, selected_tag_names):
    image_url = request.build_absolute_uri(reverse("feed:share_image", args=[item_type, item_id]))
    page_url = request.build_absolute_uri(reverse("feed:share", args=[item_type, item_id]))
    encoded_page_url = quote(page_url, safe="")
    text = f"{title}\n{body}"
    encoded_text = quote(text, safe="")

    return {
        "type": item_type,
        "id": item_id,
        "title": title,
        "body": body,
        "invalidates": _invalidates_context(item_type, item.invalidates),
        "tags": [
            {
                "name": tag.name,
                "url": _tags_url(_add_tag_name(selected_tag_names, tag.name)),
                "active": tag.name in selected_tag_names,
            }
            for tag in item.tags.all()
        ],
        "upvotes": item.upvotes,
        "downvotes": item.downvotes,
        "upvote_url": reverse("feed:vote", args=[item_type, item_id, "up"]),
        "downvote_url": reverse("feed:vote", args=[item_type, item_id, "down"]),
        "image_url": image_url,
        "share_links": [
            ("x", f"https://twitter.com/intent/tweet?url={encoded_page_url}&text={encoded_text}"),
            ("facebook", f"https://www.facebook.com/sharer/sharer.php?u={encoded_page_url}"),
            ("linkedin", f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_page_url}"),
            ("whatsapp", f"https://wa.me/?text={encoded_text}%20{encoded_page_url}"),
        ],
    }


def _interleaved_cards(fact_cards, record_cards):
    random.shuffle(fact_cards)
    random.shuffle(record_cards)
    cards = []
    longest = max(len(fact_cards), len(record_cards))

    for index in range(longest):
        if index < len(fact_cards):
            cards.append(fact_cards[index])
        if index < len(record_cards):
            cards.append(record_cards[index])

    return cards


def _invalidates_context(item_type, item):
    if not item:
        return None
    title, body = _display_parts(item_type, item)
    return {
        "anchor": f"#{item_type}-{item.id}",
        "title": title,
        "body": body,
    }


def _selected_tag_names(request):
    names = request.GET.getlist("tags")
    legacy_name = request.GET.get("tag")
    if legacy_name:
        names.append(legacy_name)
    return list(dict.fromkeys(name for name in names if name))


def _add_tag_name(selected_tag_names, tag_name):
    if tag_name in selected_tag_names:
        return selected_tag_names
    return [*selected_tag_names, tag_name]


def _tags_url(tag_names):
    if not tag_names:
        return "/"
    return f"/?{urlencode({'tags': tag_names}, doseq=True)}"


def _display_parts(item_type, item):
    if item_type == "fact":
        return f"Fact #{item.id}", item.text

    return f"Record #{item.number}", item.text


def _draw_share_card(draw, item_type, title, body, scale=1):
    card_color = "#f6fbff" if item_type == "fact" else "#fff7f7"
    title_color = "#002030" if item_type == "fact" else "#a71e1e"
    text_color = "#10212b"
    border_color = "#002030"
    card_width = 1088 * scale
    padding_x = 60 * scale
    padding_y = 54 * scale
    title_font = _font(42 * scale, bold=True)
    body_font = _font(40 * scale)
    body_line_height = 54 * scale
    title_gap = 36 * scale
    max_text_width = card_width - (padding_x * 2)
    body_lines = _wrap_text(draw, body, body_font, max_text_width)
    title_height = _text_height(draw, title, title_font)
    body_height = body_line_height * len(body_lines)
    card_height = padding_y + title_height + title_gap + body_height + padding_y
    box = _share_card_box(card_width, card_height, scale)
    left, top, right, bottom = box

    draw.rectangle(box, fill=card_color)
    _draw_jagged_edge(draw, box, border_color)

    x = left + padding_x
    y = top + padding_y

    draw.text((x, y), title, fill=title_color, font=title_font)
    y += title_height + title_gap

    for line in body_lines:
        draw.text((x, y), line, fill=text_color, font=body_font)
        y += body_line_height


def _share_card_box(width, height, scale=1):
    left = ((1200 * scale) - width) // 2
    lower_top = 300 * scale
    lower_bottom = 612 * scale
    lower_height = lower_bottom - lower_top
    top = lower_top + max((lower_height - height) // 2, 0)
    return (left, top, left + width, top + height)


def _wrap_text(draw, text, font, max_width):
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and _text_width(draw, candidate, font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def _text_height(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[3] - box[1]


def _draw_jagged_edge(draw, box, color):
    left, top, right, bottom = box
    notch = 12
    step = 34

    for x in range(left, right, step):
        draw.rectangle((x, top, x + notch, top + notch), fill=color)
        draw.rectangle((x, bottom - notch, x + notch, bottom), fill=color)

    for y in range(top, bottom, step):
        draw.rectangle((left, y, left + notch, y + notch), fill=color)
        draw.rectangle((right - notch, y, right, y + notch), fill=color)


def _font(size, bold=False):
    names = ("Arial Bold.ttf", "Arial.ttf") if bold else ("Arial.ttf",)
    for name in names:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _draw_pixel_logo(draw, canvas_width, y, scale=1):
    cell = 13 * scale
    letter_gap = 8 * scale
    word_gap = 32 * scale
    text = "sportsfacts"
    total_width = (len(text) * 5 * cell) + ((len(text) - 2) * letter_gap) + word_gap
    x = (canvas_width - total_width) // 2

    for index, letter in enumerate(text):
        if index == 6:
            x += word_gap
        color = "#ffffff" if index < 6 else "#73a8ef"
        _draw_pixel_letter(draw, letter, x + 6, y + 6, cell, "#00131d")
        _draw_pixel_letter(draw, letter, x, y, cell, color, 1)
        x += (5 * cell) + letter_gap


def _draw_pixel_letter(draw, letter, x, y, cell, color, bleed=0):
    for row_index, row in enumerate(PIXEL_LETTERS[letter]):
        for column_index, value in enumerate(row):
            if value == "1":
                left = x + (column_index * cell)
                top = y + (row_index * cell)
                draw.rectangle((left - bleed, top - bleed, left + cell - 1 + bleed, top + cell - 1 + bleed), fill=color)


def _get_item(item_type, item_id):
    model = _model_for_type(item_type)
    try:
        return model.objects.get(id=item_id)
    except model.DoesNotExist as exc:
        raise Http404 from exc


def _model_for_type(item_type):
    if item_type == "fact":
        return Fact
    if item_type == "record":
        return Record
    raise Http404
