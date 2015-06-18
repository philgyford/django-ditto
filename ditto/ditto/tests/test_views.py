from django.core.urlresolvers import reverse
from django.test import TestCase


class DittoViewTests(TestCase):

    def test_home(self):
        response = self.client.get(reverse('ditto'))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'ditto/ditto/index.html')
        self.assertTemplateUsed(response, 'ditto/ditto/base.html')



