from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Fact(models.Model):
    text = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="facts")
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"Fact #{self.pk} - {self.text}"


class Record(models.Model):
    number = models.PositiveIntegerField(unique=True)
    text = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True, related_name="records")
    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("number",)

    def __str__(self):
        return f"Record #{self.number} - {self.text}"
