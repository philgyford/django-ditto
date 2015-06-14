from django.views.generic import TemplateView


class PinboardHomeView(TemplateView):
    template_name = "ditto/pinboard/index.html"

