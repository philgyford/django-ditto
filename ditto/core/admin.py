from django.contrib import admin


class DittoItemModelAdmin(admin.ModelAdmin):
    def post_year_str(self, instance):
        "So Admin doesn't add a comma, like '2,016'."
        return str(instance.post_year)

    post_year_str.short_description = "Post year"
