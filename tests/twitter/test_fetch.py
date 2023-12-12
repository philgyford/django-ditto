import responses
from django.test import TestCase


class FetchTwitterTestCase(TestCase):
    """Parent class with commomn things."""

    api_url = "https://api.twitter.com/1.1"

    # Should be set in child classes to use self.make_response_body():
    # eg 'account/verify_credentials'
    api_call = ""

    # Should be set in child classes to use self.make_response_body():
    # eg, 'tweets.json'
    api_fixture = ""

    def make_response_body(self):
        "Makes the JSON response to a call to the API"
        with open(f"tests/twitter/fixtures/api/{self.api_fixture}") as f:
            json_data = f.read()
            return json_data

    def add_response(
        self,
        body,
        *,
        status=200,
        querystring=None,
        match_querystring=False,
        method="GET",
    ):
        """Add a Twitter API response.

        Keyword arguments:
        body -- The JSON string representing the body of the response.
        status -- Int, HTTP response status.
        querystring -- eg {'count': 200, 'user_id': 123}
        match_querystring -- You probably want this to be True if you've set
                             a querystring.
        method -- 'GET' or 'POST'.
        """
        querystring = {} if querystring is None else querystring
        url = f"{self.api_url}/{self.api_call}.json"

        if len(querystring):
            qs = "&".join(f"{key}={querystring[key]}" for key in querystring)
            url = f"{url}?{qs}"

        method = responses.POST if method == "POST" else responses.GET

        responses.add(
            method,
            url,
            status=status,
            match_querystring=match_querystring,
            body=body,
            content_type="application/json; charset=utf-8",
        )
