#!/usr/bin/env python
import flickrapi
import webbrowser

# Put your API Key and Secret here:
api_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
api_secret = 'XXXXXXXXXXXXXXXX'

flickr = flickrapi.FlickrAPI(api_key, api_secret)

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms='read'):

    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms='read')
    webbrowser.open_new_tab(authorize_url)

    print("Authorize your Flickr account in your web browser.")

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    verifier = input('Verifier code: ')

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

    print("Done!")

else:
    print("This account is already authorised.")

