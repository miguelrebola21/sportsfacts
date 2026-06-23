from io import BytesIO
import textwrap
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
    facts = Fact.objects.prefetch_related("tags")
    records = Record.objects.prefetch_related("tags")
    selected_tags = list(Tag.objects.filter(name__in=selected_tag_names))
    selected_tag_names = [tag.name for tag in selected_tags]
    cards = []

    if selected_tags:
        facts = facts.filter(tags__in=selected_tags).distinct()
        records = records.filter(tags__in=selected_tags).distinct()

    for fact in facts:
        cards.append(_card_context(request, "fact", fact, fact.id, f"Fact #{fact.id}", fact.text, selected_tag_names))

    for record in records:
        cards.append(_card_context(request, "record", record, record.id, f"Record #{record.number}", record.text, selected_tag_names))

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
    background = "#002030" if item_type == "fact" else "#9f1d1d"
    image = Image.new("RGB", (1200, 630), background)
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.load_default(size=64)
    body_font = ImageFont.load_default(size=54)

    _draw_pixel_logo(draw, image.width, 54)

    lines = [title] + textwrap.wrap(body, width=32)
    line_height = 70
    total_height = line_height * len(lines)
    y = (image.height - total_height) // 2 + 45

    for index, line in enumerate(lines):
        font = title_font if index == 0 else body_font
        _draw_centered_text(draw, line, y, font, "#ffffff", image.width)
        y += line_height

    output = BytesIO()
    image.save(output, format="PNG")
    return HttpResponse(output.getvalue(), content_type="image/png")


def _card_context(request, item_type, item, item_id, title, body, selected_tag_names):
    image_url = request.build_absolute_uri(reverse("feed:share_image", args=[item_type, item_id]))
    encoded_image_url = quote(image_url, safe="")
    text = f"{title}\n{body}"
    encoded_text = quote(text, safe="")

    return {
        "type": item_type,
        "id": item_id,
        "title": title,
        "body": body,
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
            ("x", f"https://twitter.com/intent/tweet?url={encoded_image_url}&text={encoded_text}"),
            ("facebook", f"https://www.facebook.com/sharer/sharer.php?u={encoded_image_url}"),
            ("linkedin", f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_image_url}"),
            ("whatsapp", f"https://wa.me/?text={encoded_text}%20{encoded_image_url}"),
        ],
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


def _draw_centered_text(draw, text, y, font, fill, width, x_offset=0):
    box = draw.textbbox((0, 0), text, font=font)
    x = (width - (box[2] - box[0])) // 2 + x_offset
    draw.text((x, y), text, fill=fill, font=font)


def _draw_pixel_logo(draw, canvas_width, y):
    cell = 13
    letter_gap = 8
    word_gap = 32
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
