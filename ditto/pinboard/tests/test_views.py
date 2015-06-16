from django.core.urlresolvers import reverse
from django.test import TestCase


class PinboardViewTests(TestCase):

    def test_home(self):
        response = self.client.get(reverse('pinboard_home'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ditto/pinboard/index.html')
        self.assertTemplateUsed(response, 'ditto/pinboard/base.html')
        self.assertTemplateUsed(response, 'ditto/core/base.html')

