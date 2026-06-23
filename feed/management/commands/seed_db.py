from django.core.management.base import BaseCommand

from feed.models import Fact, Record, Tag


class Command(BaseCommand):
    help = "Seed the database with sample sports facts and records."

    def handle(self, *args, **options):
        basketball, _ = Tag.objects.get_or_create(name="basketball")
        football, _ = Tag.objects.get_or_create(name="football")

        fact, _ = Fact.objects.get_or_create(text="Blgvaskjfadksfa")
        fact.tags.add(basketball)

        record, _ = Record.objects.get_or_create(
            number=232,
            defaults={"text": "dlkaflasdklfkdasf"},
        )
        record.tags.add(football)

        self.stdout.write(self.style.SUCCESS("seeded sports facts database"))
