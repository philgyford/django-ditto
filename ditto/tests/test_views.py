from django.core.urlresolvers import reverse
from django.test import TestCase



class DittoTests(TestCase):

    def test_home(self):
        response = self.client.get(reverse('home'))
        self.assertEquals(response.status_code, 200)

