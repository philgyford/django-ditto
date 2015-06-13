from django.views.generic import TemplateView


class DittoHomeView(TemplateView):
    template_name = "ditto/home.html"

