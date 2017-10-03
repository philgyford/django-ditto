import datetime
import json
import pytz

from django.db.utils import IntegrityError

from taggit.models import Tag

from . import FetchError
from ..models import Photo, Photoset, User


# These classes are passed JSON data from the Flickr API and create/update
# objects based on that.
#
# They don't do any fetching of data or files themselves.

# CLASSES HERE:
#
# SaveUtilsMixin
#
# UserSaver
# PhotoSaver
# PhotosetSaver


class SaveUtilsMixin(object):
    """Handy utility methods used by the *Saver classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _api_datetime_to_datetime(self, api_time, timezone_id=None):
        """Change a text datetime from the API to a datetime with timezone.
        api_time is a string like "1956-01-01 00:00:00".
        timezone_id is a TZ timezone name like 'Africa/Accra'
        """
        if timezone_id is None or timezone_id == '':
            timezone_id = 'Etc/UTC'
        tz = pytz.timezone(timezone_id)
        return datetime.datetime.strptime(
                            api_time, '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz)

    def _unixtime_to_datetime(self, api_time):
        """Change a text unixtime from the API to a datetime with timezone.
        api_time is a string or int like "1093459273".
        """
        return datetime.datetime.utcfromtimestamp(
                                        int(api_time)).replace(tzinfo=pytz.utc)


class UserSaver(SaveUtilsMixin, object):
    """For creating/updating an individual User based on data from the API.

    Use like:

        UserSaver().save_user(data, fetch_time)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_user(self, user, fetch_time):
        """
        Keyword arguments:
        user -- A dict of the data about a user from the API's JSON.
        fetch_time -- A datetime.

        Returns the User object that was created or updated.
        """
        raw_json = json.dumps(user)

        defaults = {
            'fetch_time':   fetch_time,
            'raw':          raw_json,
            'nsid':         user['nsid'],
            'is_pro':       (int(user['ispro']) == 1),
            'iconserver':   user['iconserver'],
            'iconfarm':     user['iconfarm'],
            'username':     user['username']['_content'],
            'realname':     user['realname']['_content'],
            'location':     user['location']['_content'],
            'description':  user['description']['_content'],
            'photos_url':   user['photosurl']['_content'],
            'profile_url':  user['profileurl']['_content'],
            'photos_count': int(user['photos']['count']['_content']),
            'photos_first_date': self._unixtime_to_datetime(
                                user['photos']['firstdate']['_content']),
            'photos_first_date_taken': self._api_datetime_to_datetime(
                                user['photos']['firstdatetaken']['_content']),
            'timezone_id':  user['timezone']['timezone_id'],
        }

        if 'views' in user['photos']:
            # I think this might only be returned for the Account's own user.
            defaults['photos_views'] = \
                                    int(user['photos']['views']['_content'])

        user_obj, created = User.objects.update_or_create(
            nsid=user['nsid'], defaults=defaults
        )

        return user_obj


class PhotoSaver(SaveUtilsMixin, object):
    """For creating/updating an individual Photo based on data from the API.

    Use like:

        PhotoSaver().save_photo(data, fetch_time)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_photo(self, photo):
        """Takes a dict of photo data from the API and creates or updates a
        Photo object.

        Keyword arguments:
        photo -- The photo data, from several Flickr API calls.
                 Has keys:
                     'fetch_time': A datetime.
                     'user_obj': User object for this photo's owner.
                     'info': Results of a photos.getInfo call.
                     'exif': Results of a photos.getExif call.
                     'sizes': Results of a photos.getSizes call.

        Returns:
        The Photo object that was created or updated.
        """

        # photo['info']['urls'] = {
        #     'url': [ {'type':'photopage', '_content':'http...'} ]
        # }
        permalink = next(url for url in photo['info']['urls']['url'] if url['type'] == 'photopage')['_content']

        defaults = {
            # DittoItemModel fields
            'title':                photo['info']['title']['_content'],
            'permalink':            permalink,
            'is_private':           (photo['info']['visibility']['ispublic'] == 0),
            'fetch_time':           photo['fetch_time'],
            'post_time':            self._unixtime_to_datetime(
                                            photo['info']['dates']['posted']),
            'raw':                  json.dumps(photo['info']),

            # Photo fields
            'user':                 photo['user_obj'],
            'flickr_id':            photo['info']['id'],
            'description':          photo['info']['description']['_content'],
            'secret':               photo['info']['secret'],
            'original_secret':      photo['info']['originalsecret'],
            'server':               photo['info']['server'],
            'farm':                 photo['info']['farm'],
            'license':              photo['info']['license'],
            'rotation':             photo['info']['rotation'],
            'original_format':      photo['info']['originalformat'],
            'safety_level':         photo['info']['safety_level'],
            'has_people':           (int(photo['info']['people']['haspeople']) == 1),
            'last_update_time':     self._unixtime_to_datetime(
                                        photo['info']['dates']['lastupdate']),
            'taken_time':           self._api_datetime_to_datetime(
                                                photo['info']['dates']['taken'],
                                                photo['user_obj'].timezone_id),
            'taken_granularity':    \
                            int(photo['info']['dates']['takengranularity']),
            'taken_unknown':        \
                            (int(photo['info']['dates']['takenunknown']) == 1),
            'view_count':           photo['info']['views'],
            'comment_count':        photo['info']['comments']['_content'],
            'media':                photo['info']['media'],

            # Location fields

            # Sizes fields
            'sizes_raw':            json.dumps(photo['sizes']),

            # EXIF fields
            'exif_raw':             json.dumps(photo['exif']),
            'exif_camera':          photo['exif']['camera'],
        }

        # Photos with no location have these fields missing entirely:
        if 'geoperms' in photo['info']:
            defaults['geo_is_private']      = (int(photo['info']['geoperms']['ispublic']) == 0)

        if 'location' in photo['info']:
            loc = photo['info']['location']
            defaults['latitude']            = loc['latitude']
            defaults['longitude']           = loc['longitude']
            defaults['location_accuracy']   = loc['accuracy']
            defaults['location_context']    = loc['context']
            if 'place_id' in loc:
                defaults['location_place_id']   = loc['place_id']
            if 'woeid' in loc:
                defaults['location_woeid']      = loc['woeid']
            if 'locality' in loc:
                defaults['locality_name']       = loc['locality']['_content']
                defaults['locality_place_id']   = loc['locality']['place_id']
                defaults['locality_woeid']      = loc['locality']['woeid']
            if 'county' in loc:
                defaults['county_name']         = loc['county']['_content']
                defaults['county_place_id']     = loc['county']['place_id']
                defaults['county_woeid']        = loc['county']['woeid']
            if 'region' in loc:
                defaults['region_name']         = loc['region']['_content']
                defaults['region_place_id']     = loc['region']['place_id']
                defaults['region_woeid']        = loc['region']['woeid']
            if 'country' in loc:
                defaults['country_name']        = loc['country']['_content']
                defaults['country_place_id']    = loc['country']['place_id']
                defaults['country_woeid']       = loc['country']['woeid']

        # The size labels for all possible sizes an image might have, that we
        # also have width/height parameters for on Photo:
        sizes = [v['label'] for k,v in Photo.PHOTO_SIZES.items()] + \
                [v['label'] for k,v in Photo.VIDEO_SIZES.items()]
        # We don't store width/height for these, so ignore them:
        sizes.remove('Square')
        sizes.remove('Large square')

        for size in photo['sizes']['size']:
            if size['label'] in sizes:
                # eg, 'Small 320' becomes 'small_320':
                name = size['label'].lower().replace(" ", "_")
                defaults[name+'_width'] = int(size['width'])
                defaults[name+'_height'] = int(size['height'])

        try:
            for e in photo['exif']['exif']:
                if e['tag'] == 'LensModel':
                    defaults['exif_lens_model'] = e['raw']['_content']
                elif e['tag'] == 'FNumber':
                    defaults['exif_aperture'] = e['clean']['_content']
                elif e['tag'] == 'ExposureTime':
                    defaults['exif_exposure'] = e['clean']['_content']
                elif e['tag'] == 'Flash':
                    defaults['exif_flash'] = e['raw']['_content']
                elif e['tag'] == 'FocalLength':
                    defaults['exif_focal_length'] = e['clean']['_content']
                elif e['tag'] == 'ISO':
                    defaults['exif_iso'] = e['raw']['_content']
        except KeyError:
            pass

        photo_obj, created = Photo.objects.update_or_create(
                flickr_id=photo['info']['id'],
                defaults=defaults
            )

        self._save_tags(photo_obj, photo['info']['tags']['tag'])

        return photo_obj

    def _save_tags(self, photo_obj, tags_data):
        """
        Adds/deletes tags for a photo.

        Required Arguments
          photo_obj: The Photo object we're altering tags for.
          photo_user_obj: The User whose photo this is (because they're most
                            likely to have created the tags.)
          tags_data: A list of dicts about the tags, straight from the API.
        """

        # The existing tag-photo relationships.
        tagged_photos = Photo.tags.through.objects.filter(
                                                   content_object=photo_obj)

        local_flickr_ids = set([])
        remote_flickr_ids = set([])

        # Get the Flickr IDs of all the current tag-photo relationships.
        for tagged_photo in tagged_photos:
            local_flickr_ids.add(tagged_photo.flickr_id)

        for tag in tags_data:
            remote_flickr_ids.add(tag['id'])

            if tag['id'] not in local_flickr_ids:

                # This tag isn't currently on the photo, so add it.
                try:
                    tag_obj, tag_created = Tag.objects.get_or_create(
                        slug=tag['_content'], defaults={ 'name':tag['raw'] }
                    )
                except IntegrityError:
                    # It's possible for there to be a tag with a different
                    # slug but the same name, which would cause an
                    # IntegrityError.
                    # In which case, just fetch the existing Tag by name:
                    tag_obj = Tag.objects.get(name=tag['raw'])

                # Who created this tag?
                if tag['author'] == photo_obj.user.nsid:
                    # The same person whose photo these tags are on.
                    user = photo_obj.user
                else:
                    # In theory we'll already have fetched and saved data for
                    # all authors of these tags when fetching this photo's
                    # data.
                    try:
                        user = User.objects.get(nsid=tag['author'])
                    except User.DoesNotExist:
                        raise FetchError("Tried to add a Tag authored by a Flickr user with NSID %s who doesn't exist in the DB." % tag['author'])

                pt_obj = Photo.tags.through(
                            flickr_id = tag['id'],
                            author = user,
                            machine_tag = (tag['machine_tag'] == "1"),
                            content_object = photo_obj,
                            tag = tag_obj
                        )
                pt_obj.save()

        flickr_ids_to_delete = local_flickr_ids.difference(remote_flickr_ids)

        # Finally, delete any tag-photo relationships which were identified
        # above as no longer on the photo on Flickr.
        for tagged_photo in tagged_photos:
            if tagged_photo.flickr_id in flickr_ids_to_delete:
                tagged_photo.delete()


class PhotosetSaver(SaveUtilsMixin, object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_photoset(self, photoset):
        """Takes a dict of photoset data from the API and creates or updates a
        Photoset object.

        It accepts a list of photo data, but will only add each photo to the
        photoset if we already have that photo's data in the DB.

        Keyword arguments:
        photoset -- Has keys:
                    'fetch_time': A datetime.
                    'photoset': The data about the photoset from the API.
                    'photos': The data about the set's photos from the API.
                    'user_obj': User object for this photoset's owner.

        Returns:
        The Photoset object that was created or updated.
        """

        ps = photoset['photoset']

        defaults = {
            'fetch_time':           photoset['fetch_time'],
            'user':                 photoset['user_obj'],
            'flickr_id':            ps['id'],
            'title':                ps['title']['_content'],
            'description':          ps['description']['_content'],
            'photo_count':          ps['photos'],
            'video_count':          ps['videos'],
            'view_count':           ps['count_views'],
            'comment_count':        ps['count_comments'],
            'last_update_time':     self._unixtime_to_datetime(
                                                            ps['date_update']),
            'flickr_created_time':  self._unixtime_to_datetime(
                                                            ps['date_create']),
            'raw':                  json.dumps(ps),
            'photos_raw':           json.dumps(photoset['photos']),
        }

        try:
            defaults['primary_photo'] = \
                                    Photo.objects.get(flickr_id=ps['primary'])
        except Photo.DoesNotExist:
            pass

        photoset_obj, created = Photoset.objects.update_or_create(
                flickr_id=ps['id'],
                defaults=defaults
            )

        if photoset_obj:
            # Add all the photoset's photos that we have in the DB to the
            # photoset object.
            photos = []
            for photo in photoset['photos']:
                try:
                    photos.append( Photo.objects.get(flickr_id=photo['id']) )
                except Photo.DoesNotExist:
                    pass

            # Sets/updates the SortedManyToMany field of the photoset's photos:
            photoset_obj.photos = photos

        return photoset_obj

