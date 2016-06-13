import datetime
import json
import pytz
from decimal import Decimal
from unittest.mock import patch

from freezegun import freeze_time

from taggit.models import Tag

from .test_fetch import FlickrFetchTestCase
from ditto.flickr.factories import PhotoFactory, UserFactory
from ditto.flickr.fetch import FetchError
from ditto.flickr.fetch.savers import UserSaver, PhotosetSaver, PhotoSaver
from ditto.flickr.models import Photo, Photoset, TaggedPhoto, User


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
    @patch.object(PhotoSaver, '_save_tags')
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
        self.assertFalse(photo.has_people)
        self.assertEqual(photo.last_update_time, datetime.datetime.strptime(
                                    '2016-04-04 13:21:11', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(photo.taken_time, datetime.datetime.strptime(
                            '2016-03-17 16:25:15', '%Y-%m-%d %H:%M:%S'
                        ).replace(tzinfo=pytz.timezone('America/Los_Angeles')))
        self.assertEqual(photo.taken_granularity, 0)
        self.assertFalse(photo.taken_unknown)
        self.assertEqual(photo.view_count, 55)
        self.assertEqual(photo.comment_count, 2)
        self.assertEqual(photo.media, 'photo')

        # Location fields
        self.assertFalse(photo.geo_is_private)
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
            'thumbnail':    (100, 77),
            'small':        (240, 186),
            'small_320':    (320, 248),
            'medium':       (500, 387),
            'medium_640':   (640, 496),
            'medium_800':   (800, 620),
            'large':        (1024, 793),
            'large_1600':   (1600, 1239),
            'large_2048':   (2048, 1585),
            'original':     (3772, 2920),
        }
        for name, wh in sizes.items():
            self.assertEqual(getattr(photo, name+'_width'), wh[0])
            self.assertEqual(getattr(photo, name+'_height'), wh[1])

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

    @patch.object(PhotoSaver, '_save_tags')
    def test_saves_photo_with_no_exif(self, save_tags):
        "If it has no EXIF data it doesn't complain."

        photo_data = self.make_photo_data()
        del(photo_data['exif']['exif'])
        photo = self.make_photo_object( photo_data )
        self.assertEqual(photo.flickr_id, int(photo_data['info']['id']))

    @patch.object(PhotoSaver, '_save_tags')
    def test_saves_video_data(self, save_tags):
        photo_data = self.make_photo_data()
        # Change to use the getSizes fixture including video data:
        photo_data['sizes'] = self.load_fixture('photos.getSizes_video')['sizes']
        photo_data['info']['media'] = 'video'

        photo = self.make_photo_object( photo_data )

        self.assertEqual(photo.media, 'video')

        sizes = {
            'mobile_mp4':       (480, 360),
            'site_mp4':         (640, 360),
            'hd_mp4':           (1282, 720),
            'video_original':   (1280, 720),
        }
        for name, wh in sizes.items():
            self.assertEqual(getattr(photo, name+'_width'), wh[0])
            self.assertEqual(getattr(photo, name+'_height'), wh[1])

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    @patch.object(PhotoSaver, '_save_tags')
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
                            medium_width=300,
                            medium_height=200,
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
        self.assertEqual(photo.medium_width, 500)
        self.assertEqual(photo.medium_height, 387)
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
                self.assertFalse(tp.machine_tag)
                self.assertEqual(tp.author, user_2)
                self.assertEqual(tp.flickr_id, '5827-26069027966-1200699')
            else:
                self.assertEqual(tp.author, user_1)
            if tp.tag.slug == 'tester:foo=bar':
                self.assertTrue(tp.machine_tag)

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

    @patch.object(PhotoSaver, '_save_tags')
    def test_handles_photos_with_no_location(self, save_tags):
        photo_data = self.make_photo_data()
        del photo_data['info']['location']
        del photo_data['info']['geoperms']

        photo = self.make_photo_object( photo_data )
        self.assertEqual(photo.location_place_id, '')
        self.assertEqual(photo.location_woeid, '')
        self.assertEqual(photo.latitude, None)
        self.assertEqual(photo.longitude, None)


class PhotosetSaverTestCase(FlickrFetchTestCase):

    def make_photoset_object(self, photoset_data):
        """"Creates/updates a Photo from API data, then fetches that Photo from
        the DB and returns it.
        """
        saved_photoset = PhotosetSaver().save_photoset(photoset_data)
        return Photoset.objects.get(flickr_id=72157665648859705)

    def make_photoset_data(self):
        """Makes the dict of data that photo_save() expects, based on API data.
        """
        return {
            'fetch_time': datetime.datetime.utcnow().replace(tzinfo=pytz.utc),
            'user_obj': UserFactory(nsid='35034346050@N01'),
            'photoset': self.load_fixture('photosets.getList')['photosets']['photoset'][0],
            'photos': self.load_fixture('photosets.getPhotos')['photoset']['photo'],
        }

    @freeze_time("2015-08-14 12:00:00", tz_offset=-8)
    def test_saves_correct_photoset_data(self):

        photoset_data = self.make_photoset_data()
        photoset = self.make_photoset_object( photoset_data )

        self.assertEqual(photoset.fetch_time,
                        datetime.datetime.utcnow().replace(tzinfo=pytz.utc))
        self.assertEqual(photoset.user, photoset_data['user_obj'])

        self.assertEqual(photoset.flickr_id, 72157665648859705)
        self.assertEqual(photoset.title, 'Old Postcards of Walton-on-the-Naze')
        self.assertEqual(photoset.description, '<b>Some text here</b>\n\nAnd new lines!')
        self.assertEqual(photoset.photo_count, 5)
        self.assertEqual(photoset.video_count, 1)
        self.assertEqual(photoset.view_count, 7)
        self.assertEqual(photoset.comment_count, 3)
        self.assertEqual(photoset.last_update_time, datetime.datetime.strptime(
                                    '2016-03-28 16:02:03', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(photoset.flickr_created_time, datetime.datetime.strptime(
                                    '2016-03-08 19:37:04', '%Y-%m-%d %H:%M:%S'
                                ).replace(tzinfo=pytz.utc))
        self.assertEqual(photoset.raw, json.dumps(photoset_data['photoset']))
        self.assertEqual(photoset.photos_raw,
                                        json.dumps(photoset_data['photos']))

        self.assertEqual(photoset.primary_photo, None)

    def test_adds_primary_photo(self):
        "If the primary photo is in the DB, it's set."

        photo = PhotoFactory(flickr_id=24990464004)

        photoset_data = self.make_photoset_data()
        photoset = self.make_photoset_object( photoset_data )

        self.assertEqual(photoset.primary_photo, photo)

    def test_adds_photos(self):
        "Will add all the photos to the photoset if they're in the DB."

        # The photos' Flickr IDs from the fixture:
        photo_ids = [
            24990464004, 25253437489, 25253471989, 25502409002, 25253527909,
        ]
        for id in photo_ids:
            PhotoFactory(flickr_id=id)

        photoset_data = self.make_photoset_data()
        photoset = self.make_photoset_object( photoset_data )

        self.assertEqual(photoset.photos.count(), 5)
        photos = photoset.photos.all()

        self.assertEqual(photos[0].flickr_id, photo_ids[0])
        self.assertEqual(photos[2].flickr_id, photo_ids[2])
        self.assertEqual(photos[4].flickr_id, photo_ids[4])

    def test_skips_photos_not_in_db(self):
        "If we don't have a photo in the db, it's not added to photoset."

        # Three of the five photos' Flickr IDs from the fixture:
        photo_ids = [
            24990464004, 25253437489, 25502409002,
        ]
        for id in photo_ids:
            PhotoFactory(flickr_id=id)

        photoset_data = self.make_photoset_data()
        photoset = self.make_photoset_object( photoset_data )

        self.assertEqual(photoset.photos.count(), 3)

