import datetime
import json
import pytz
from decimal import Decimal
from unittest.mock import patch
from freezegun import freeze_time

from taggit.models import Tag

from .test_fetch import FlickrFetchTestCase
from ..factories import PhotoFactory, UserFactory
from ..fetch import FetchError, UserSaver, PhotoSaver
from ..models import Photo, TaggedPhoto, User


class UserSaverTestCase(FlickrFetchTestCase):
    """Test creating/updating Users from API data."""

    def make_user_object(self, user_data):
        """"Creates/updates a User from API data, then fetches that User from
        the DB and returns it.
        """
        fetch_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        saved_user = UserSaver().save_user(user_data, fetch_time)
        return User.objects.get(nsid="35034346050@N01")

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_user_data(self):
        """Passing save_user() data from the API should create a new User."""

        user_data = self.load_fixture('people.getInfo')
        user = self.make_user_object(user_data['person'])

        self.assertEqual(user.fetch_time,
                            datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
        self.assertEqual(user.raw, json.dumps(user_data['person']))
        self.assertEqual(user.nsid, "35034346050@N01")
        self.assertTrue(user.is_pro)
        self.assertEqual(user.iconserver, 7420)
        self.assertEqual(user.iconfarm, 8)
        self.assertEqual(user.username, 'Phil Gyford')
        self.assertEqual(user.realname, 'Phil Gyford')
        self.assertEqual(user.location, 'London, UK')
        self.assertEqual(user.description, 'A test description.')
        self.assertEqual(
                user.photos_url, 'https://www.flickr.com/photos/philgyford/')
        self.assertEqual(
                user.profile_url, 'https://www.flickr.com/people/philgyford/')
        self.assertEqual(user.photos_count, 2876)
        self.assertEqual(user.photos_first_date, datetime.datetime.utcfromtimestamp(1093459273).replace(tzinfo=pytz.utc))
        self.assertEqual(user.photos_first_date_taken,
                                datetime.datetime.strptime(
                                    '1956-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(user.photos_views, 227227)
        self.assertEqual(user.timezone_id, 'Europe/London')

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_updates_existing_user(self):
        """Passing save_user() data from the API should update an existing
        User.
        """
        # Some data that will be updated:
        existing_user = User(nsid="35034346050@N01",
                            iconfarm=3,
                            is_pro=False,
                            username="Bob",
                            location="San Francisco",
                            photos_count=3,
                            photos_views=3)
        existing_user.save()

        user_data = self.load_fixture('people.getInfo')
        user = self.make_user_object(user_data['person'])

        self.assertTrue(user.is_pro)
        self.assertEqual(user.username, 'Phil Gyford')
        self.assertEqual(user.location, 'London, UK')
        self.assertEqual(user.photos_count, 2876)
        self.assertEqual(user.photos_views, 227227)


class PhotoSaverTestCase(FlickrFetchTestCase):

    def make_photo_object(self, photo_data):
        """"Creates/updates a Photo from API data, then fetches that Photo from
        the DB and returns it.
        """
        saved_photo = PhotoSaver().save_photo(photo_data)
        return Photo.objects.get(flickr_id="26069027966")

    def make_photo_data(self):
        """Makes the dict of data that photo_save() expects, based on API data.
        """
        return {
            'fetch_time': datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
            'user_obj': UserFactory(nsid='35034346050@N01'),
            'info': self.load_fixture('photos.getInfo')['photo'],
            'exif': self.load_fixture('photos.getExif')['photo'],
            'sizes': self.load_fixture('photos.getSizes')['sizes'],
        }

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch('ditto.flickr.fetch.PhotoSaver._save_tags')
    def test_saves_correct_photo_data(self, save_tags):
        """Passing save_photo() data from the API should create a new Photo."""

        photo_data = self.make_photo_data()
        photo = self.make_photo_object( photo_data )

        # DittoItemModel fields
        self.assertEqual(photo.title, 'Dore Abbey')
        self.assertEqual(photo.permalink, 'https://www.flickr.com/photos/philgyford/26069027966/')
        self.assertFalse(photo.is_private)
        self.assertEqual(photo.summary, "Some test HTML. And another paragraph.")
        self.assertEqual(photo.fetch_time,
                            datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
        self.assertEqual(photo.post_time, datetime.datetime.strptime(
                                    '2016-03-28 16:05:05', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(photo.latitude, Decimal('51.967930000'))
        self.assertEqual(photo.longitude, Decimal('-2.894419000'))
        self.assertEqual(photo.raw, json.dumps(photo_data['info']))

        # Photo fields
        self.assertEqual(photo.user, photo_data['user_obj'])
        self.assertEqual(photo.flickr_id, 26069027966)
        self.assertEqual(photo.description,
                        "Some <b>test HTML</b>.\n\nAnd another paragraph.")
        self.assertEqual(photo.secret, 'abcd123456')
        self.assertEqual(photo.original_secret, 'abcd098765f')
        self.assertEqual(photo.server, '1576')
        self.assertEqual(photo.farm, 2)
        self.assertEqual(photo.license, '1')
        self.assertEqual(photo.rotation, 0)
        self.assertEqual(photo.original_format, 'jpg')
        self.assertEqual(photo.safety_level, 0)
        self.assertEqual(photo.has_people, 0)
        self.assertEqual(photo.last_update_time, datetime.datetime.strptime(
                                    '2016-04-04 13:21:11', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(photo.taken_time, datetime.datetime.strptime(
                            '2016-03-17 16:25:15', '%Y-%m-%d %H:%M:%S'
                        ).replace(tzinfo=pytz.timezone('America/Los_Angeles')))
        self.assertEqual(photo.taken_granularity, 0)
        self.assertEqual(photo.taken_unknown, 0)
        self.assertEqual(photo.view_count, 55)
        self.assertEqual(photo.comment_count, 2)
        self.assertEqual(photo.media, 'photo')

        # Location fields
        self.assertEqual(photo.geo_is_private, 0)
        self.assertEqual(photo.location_accuracy, 16)
        self.assertEqual(photo.location_context, 0)
        self.assertEqual(photo.location_place_id, "RZ9p3HlQUrt5wg")
        self.assertEqual(photo.location_woeid, '10178')
        self.assertEqual(photo.locality_name, 'Abbey Dore')
        self.assertEqual(photo.locality_place_id, 'RZ9p3HlQUrt5wg')
        self.assertEqual(photo.locality_woeid, '10178')
        self.assertEqual(photo.county_name, 'Herefordshire')
        self.assertEqual(photo.county_place_id, '7O4FecxQULxfINbBfQ')
        self.assertEqual(photo.county_woeid, '12602187')
        self.assertEqual(photo.region_name, 'England')
        self.assertEqual(photo.region_place_id, '2eIY2QFTVr_DwWZNLg')
        self.assertEqual(photo.region_woeid, '24554868')
        self.assertEqual(photo.country_name, 'United Kingdom')
        self.assertEqual(photo.country_place_id, 'cnffEpdTUb5v258BBA')
        self.assertEqual(photo.country_woeid, '23424975')

        # Sizes fields
        self.assertEqual(photo.sizes_raw, json.dumps(photo_data['sizes']))
        sizes = {
            't': (100, 77),
            'm': (240, 186),
            'n': (320, 248),
            'z': (640, 496),
            'c': (800, 620),
            'b': (1024, 793),
            'h': (1600, 1239),
            'k': (2048, 1585),
            'o': (3772, 2920),
        }
        for letter, wh in sizes.items():
            self.assertEqual(getattr(photo, 'width_'+letter), wh[0])
            self.assertEqual(getattr(photo, 'height_'+letter), wh[1])
        # Medium sizes don't have a 'letter':
        self.assertEqual(photo.width, 500)
        self.assertEqual(photo.height, 387)

        # EXIF
        self.assertEqual(photo.exif_raw, json.dumps(photo_data['exif']))
        self.assertEqual(photo.exif_camera, 'Sony NEX-6')
        self.assertEqual(photo.exif_lens_model, 'E PZ 16-50mm F3.5-5.6 OSS')
        self.assertEqual(photo.exif_aperture, 'f/13.0')
        self.assertEqual(photo.exif_exposure, '0.01 sec (1/100)')
        self.assertEqual(photo.exif_flash, 'Off, Did not fire')
        self.assertEqual(photo.exif_focal_length, '38 mm')
        self.assertEqual(photo.exif_iso, 100)

        save_tags.assert_called_once_with(photo, photo_data['info']['tags']['tag'])


    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch('ditto.flickr.fetch.PhotoSaver._save_tags')
    def test_updates_existing_photo(self, save_tags):
        """Passing save_photo() data from the API should update an existing
        Photo.
        """
        # Some data that will be updated:
        existing_photo = Photo(
                            flickr_id="26069027966",
                            user=UserFactory(),
                            secret='1234567890',
                            license='7',
                            farm=1,
                            safety_level=3,
                            title="An abbey",
                            description="A description",
                            is_private=True,
                            width=300,
                            height=200,
                            exif_camera='Sony')
        existing_photo.save()

        photo_data = self.make_photo_data()
        photo = self.make_photo_object( photo_data )

        self.assertEqual(photo.secret, 'abcd123456')
        self.assertEqual(photo.license,'1')
        self.assertEqual(photo.farm, 2)
        self.assertEqual(photo.safety_level, 0)
        self.assertEqual(photo.title, 'Dore Abbey')
        self.assertEqual(photo.summary, "Some test HTML. And another paragraph.")
        self.assertEqual(photo.description,
                        "Some <b>test HTML</b>.\n\nAnd another paragraph.")
        self.assertFalse(photo.is_private)
        self.assertEqual(photo.width, 500)
        self.assertEqual(photo.height, 387)
        self.assertEqual(photo.exif_camera, 'Sony NEX-6')

    def test_creates_tags(self):
        """Saving tags should create all the tags and tagged_photos' data."""
        photo_info_data = self.load_fixture('photos.getInfo')['photo']
        user_1 = UserFactory(nsid="35034346050@N01")
        user_2 = UserFactory(nsid="12345678901@N01")
        photo = PhotoFactory(user=user_1)

        PhotoSaver()._save_tags(photo, photo_info_data['tags']['tag'])

        tags = photo.tags.all()
        tagged_photos = TaggedPhoto.objects.filter(content_object=photo)

        # Check we've saved both tags and the through model objects.
        self.assertEqual(len(tags), 7)
        self.assertEqual(len(tagged_photos), 7)

        # Check we've saved all the stuff on the through model correctly.
        for tp in tagged_photos:
            if tp.tag.slug == 'abbeydore':
                self.assertEqual(tp.tag.name, 'Abbey Dore')
                self.assertEqual(tp.machine_tag, False)
                self.assertEqual(tp.author, user_2)
                self.assertEqual(tp.flickr_id, '5827-26069027966-1200699')
            else:
                self.assertEqual(tp.author, user_1)
            if tp.tag.slug == 'tester:foo=bar':
                self.assertEqual(tp.machine_tag, True)

    def test_syncs_tags(self):
        """If a photo already has some tags, and we save_tags, the final set
        of tags should match the new set of tags, deleting unused
        relationships."""

        photo_info_data = self.load_fixture('photos.getInfo')['photo']
        user_1 = UserFactory(nsid="35034346050@N01")
        user_2 = UserFactory(nsid="12345678901@N01")
        photo = PhotoFactory(user=user_1)

        # Create an initial tag on the photo.
        tag = Tag.objects.create(slug='initial', name='Initial')
        tagged_photo = Photo.tags.through(
                flickr_id='12345', author=user_1, content_object=photo, tag=tag)
        tagged_photo.save()
        tag_slugs = photo.tags.slugs()

        # Check starting state:
        self.assertIn('initial', tag_slugs)
        self.assertEqual(len(tag_slugs), 1)

        # Save new tags:
        PhotoSaver()._save_tags(photo, photo_info_data['tags']['tag'])
        tag_slugs = photo.tags.slugs()

        # Check that first tag has gone and the rest are there:
        self.assertNotIn('initial', tag_slugs)
        self.assertEqual(len(tag_slugs), 7)

    def test_throws_error_if_tag_author_doesnt_exist(self):
        photo_info_data = self.load_fixture('photos.getInfo')['photo']
        photo = PhotoFactory()

        with self.assertRaises(FetchError):
            PhotoSaver()._save_tags(photo, photo_info_data['tags']['tag'])

    @patch('ditto.flickr.fetch.PhotoSaver._save_tags')
    def test_handles_photos_with_no_location(self, save_tags):
        photo_data = self.make_photo_data()
        del photo_data['info']['location']
        del photo_data['info']['geoperms']

        photo = self.make_photo_object( photo_data )
        self.assertEqual(photo.location_place_id, '')
        self.assertEqual(photo.location_woeid, '')
        self.assertEqual(photo.latitude, None)
        self.assertEqual(photo.longitude, None)


