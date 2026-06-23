from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path

from .models import Fact, Record, Tag
from .xlsx import export_global_xlsx, export_xlsx, import_global_xlsx, import_xlsx


def global_export_xlsx_view(request):
    content = export_global_xlsx()
    response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="sportsfacts.xlsx"'
    return response


def global_import_xlsx_view(request):
    if request.method == "POST" and request.FILES.get("xlsx_file"):
        result = import_global_xlsx(request.FILES["xlsx_file"])
        messages.success(request, f"Imported {result['tags']} tags, {result['facts']} facts, {result['records']} records.")
        return redirect("../")

    return render(
        request,
        "admin/feed/import_xlsx.html",
        {
            **admin.site.each_context(request),
            "title": "Import all sportsfacts data from XLSX",
        },
    )


_admin_get_urls = admin.site.get_urls


def get_urls_with_global_xlsx():
    urls = _admin_get_urls()
    custom_urls = [
        path("feed/import-xlsx/", admin.site.admin_view(global_import_xlsx_view), name="feed_global_import_xlsx"),
        path("feed/export-xlsx/", admin.site.admin_view(global_export_xlsx_view), name="feed_global_export_xlsx"),
    ]
    return custom_urls + urls


admin.site.get_urls = get_urls_with_global_xlsx


class XlsxAdminMixin:
    change_list_template = "admin/feed/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-xlsx/", self.admin_site.admin_view(self.import_xlsx_view), name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_import_xlsx"),
            path("export-xlsx/", self.admin_site.admin_view(self.export_xlsx_view), name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_export_xlsx"),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["xlsx_import_url"] = "import-xlsx/"
        extra_context["xlsx_export_url"] = "export-xlsx/"
        extra_context["global_xlsx_import_url"] = "/admin/feed/import-xlsx/"
        extra_context["global_xlsx_export_url"] = "/admin/feed/export-xlsx/"
        return super().changelist_view(request, extra_context=extra_context)

    def export_xlsx_view(self, request):
        content = export_xlsx(self.model, self.get_queryset(request))
        response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{self.model._meta.model_name}.xlsx"'
        return response

    def import_xlsx_view(self, request):
        if request.method == "POST" and request.FILES.get("xlsx_file"):
            imported = import_xlsx(self.model, request.FILES["xlsx_file"])
            self.message_user(request, f"Imported {imported} rows.", messages.SUCCESS)
            return redirect("..")

        return render(
            request,
            "admin/feed/import_xlsx.html",
            {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "title": f"Import {self.model._meta.verbose_name_plural} from XLSX",
            },
        )


@admin.register(Tag)
class TagAdmin(XlsxAdminMixin, admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Fact)
class FactAdmin(XlsxAdminMixin, admin.ModelAdmin):
    list_display = ("id", "text", "upvotes", "downvotes", "created_at")
    search_fields = ("text", "tags__name")
    list_filter = ("tags",)
    filter_horizontal = ("tags",)


@admin.register(Record)
class RecordAdmin(XlsxAdminMixin, admin.ModelAdmin):
    list_display = ("number", "text", "upvotes", "downvotes", "created_at")
    search_fields = ("text", "tags__name")
    list_filter = ("tags",)
    filter_horizontal = ("tags",)
