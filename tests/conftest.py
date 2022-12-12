"""
Pytest configuration file for the tests.

Shared fixtures go here.
"""

# pylint: disable=line-too-long

import os
import pytest

from nlp4all import create_app
from nlp4all.helpers import database
from nlp4all.models import User


# hook for debugging
if os.getenv('_PYTEST_RAISE', "0") != "0":
    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        """Raise exception on interact mode."""
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        """Raise exception on internal error."""
        raise excinfo.value


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    nlp4all_app = create_app("testing")
    with nlp4all_app.app_context():
        database.init_db()
        yield nlp4all_app


@pytest.fixture
def csvdata():
    """Return a list of dicts with CSV data.
    Excerpt from:
    https://github.com/fivethirtyeight/russian-troll-tweets/master/IRAhandle_tweets_1.csv
    """
    return r'''external_author_id,author,content,region,language,publish_date,harvested_date,following,followers,updates,post_type,account_type,retweet,account_category,new_june_2018,alt_external_id,tweet_id,article_url,tco1_step1,tco2_step1,tco3_step1
906000000000000000,10_GOP,"""We have a sitting Democrat US Senator on trial for corruption and you've barely heard a peep from the mainstream media."" ~ @nedryun https://t.co/gh6g0D1oiC",Unknown,English,10/1/2017 19:58,10/1/2017 19:59,1052,9636,253,,Right,0,RightTroll,0,905874659358453760,914580356430536707,http://twitter.com/905874659358453760/statuses/914580356430536707,https://twitter.com/10_gop/status/914580356430536707/video/1,,
906000000000000000,10_GOP,Marshawn Lynch arrives to game in anti-Trump shirt. Judging by his sagging pants the shirt should say Lynch vs. belt https://t.co/mLH1i30LZZ,Unknown,English,10/1/2017 22:43,10/1/2017 22:43,1054,9637,254,,Right,0,RightTroll,0,905874659358453760,914621840496189440,http://twitter.com/905874659358453760/statuses/914621840496189440,https://twitter.com/damienwoody/status/914568524449959937/video/1,,
906000000000000000,10_GOP,"Daughter of fallen Navy Sailor delivers powerful monologue on anthem protests, burns her NFL packers gear.  #BoycottNFL https://t.co/qDlFBGMeag",Unknown,English,10/1/2017 22:50,10/1/2017 22:51,1054,9637,255,RETWEET,Right,1,RightTroll,0,905874659358453760,914623490375979008,http://twitter.com/905874659358453760/statuses/914623490375979008,https://twitter.com/10_gop/status/913231923715198976/video/1,,
906000000000000000,10_GOP,"JUST IN: President Trump dedicates Presidents Cup golf tournament trophy to the people of Florida, Texas and Puerto Rico. https://t.co/z9wVa4djAE",Unknown,English,10/1/2017 23:52,10/1/2017 23:52,1062,9642,256,,Right,0,RightTroll,0,905874659358453760,914639143690555392,http://twitter.com/905874659358453760/statuses/914639143690555392,https://twitter.com/10_gop/status/914639143690555392/video/1,,
906000000000000000,10_GOP,"19,000 RESPECTING our National Anthem! #StandForOurAnthem🇺🇸 https://t.co/czutyGaMQV",Unknown,English,10/1/2017 2:13,10/1/2017 2:13,1050,9645,246,RETWEET,Right,1,RightTroll,0,905874659358453760,914312219952861184,http://twitter.com/905874659358453760/statuses/914312219952861184,https://twitter.com/realDonaldTrump/status/914310901855129601/video/1,,
906000000000000000,10_GOP,"Dan Bongino: ""Nobody trolls liberals better than Donald Trump."" Exactly!  https://t.co/AigV93aC8J",Unknown,English,10/1/2017 2:47,10/1/2017 2:47,1050,9644,247,,Right,0,RightTroll,0,905874659358453760,914320835325853696,http://twitter.com/905874659358453760/statuses/914320835325853696,https://twitter.com/FoxNews/status/914239496786505729/video/1,,
906000000000000000,10_GOP,🐝🐝🐝 https://t.co/MorL3AQW0z,Unknown,English,10/1/2017 2:48,10/1/2017 2:48,1050,9644,248,RETWEET,Right,1,RightTroll,0,905874659358453760,914321156466933760,http://twitter.com/905874659358453760/statuses/914321156466933760,https://twitter.com/Cernovich/status/914314644772270080/photo/1,,
906000000000000000,10_GOP,'@SenatorMenendez @CarmenYulinCruz Doesn't matter that CNN doesn't report on your crimes. This won't change the fact that you're going down.',Unknown,English,10/1/2017 2:52,10/1/2017 2:53,1050,9644,249,,Right,0,RightTroll,0,905874659358453760,914322215537119234,http://twitter.com/905874659358453760/statuses/914322215537119234,,,
906000000000000000,10_GOP,"As much as I hate promoting CNN article, here they are admitting EVERYTHING Trump said about PR relief two days ago. https://t.co/tZmSeA48oh",Unknown,English,10/1/2017 3:47,10/1/2017 3:47,1050,9646,250,,Right,0,RightTroll,0,905874659358453760,914335818503933957,http://twitter.com/905874659358453760/statuses/914335818503933957,http://www.cnn.com/2017/09/27/us/puerto-rico-aid-problem/index.html,,
906000000000000000,10_GOP,After the 'genocide' remark from San Juan Mayor the narrative has changed though. @CNN fixes it's reporting constantly.,Unknown,English,10/1/2017 3:51,10/1/2017 3:51,1050,9646,251,,Right,0,RightTroll,0,905874659358453760,914336862730375170,http://twitter.com/905874659358453760/statuses/914336862730375170,,,
906000000000000000,10_GOP,After the 'genocide' remark from San Juan Mayor the narrative has changed though. @CNN fixes its reporting constantly.,Unknown,English,10/1/2017 3:58,10/1/2017 3:58,1050,9646,251,,Right,0,RightTroll,0,905874659358453760,914338590313902080,http://twitter.com/905874659358453760/statuses/914338590313902080,,,
'''


@pytest.fixture
def jsondata():
    """Retruns a flat json dict with example tweet data.
    From: https://github.com/wenming/BigDataSamples/blob/master/twittersample/sample%20twitter%20data.txt
    """
    return r"""[{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"Fking hot weather i swear im migrating to austrailia in 3 more years","id_str":"210621131198173184","place":null,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/twitter.com\/#!\/download\/iphone\" rel=\"nofollow\"\u003ETwitter for iPhone\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:05 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/images\/themes\/theme1\/bg.png","id_str":"568286862","default_profile_image":false,"statuses_count":595,"profile_link_color":"0084B4","favourites_count":5,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2206373396\/image_normal.jpg","following":null,"profile_background_color":"C0DEED","description":"Nobody can ever affect you unless you allow yourself to be affected.","notifications":null,"profile_background_tile":false,"time_zone":null,"profile_sidebar_fill_color":"DDEEF6","listed_count":0,"contributors_enabled":false,"geo_enabled":false,"created_at":"Tue May 01 13:29:22 +0000 2012","screen_name":"Chin_Hean","follow_request_sent":null,"profile_sidebar_border_color":"C0DEED","protected":false,"url":null,"default_profile":true,"name":"\u0106hr\u00ed\u0161","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":37,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2206373396\/image_normal.jpg","id":568286862,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/images\/themes\/theme1\/bg.png","utc_offset":null,"friends_count":65,"profile_text_color":"333333","location":"Stark Industries"},"retweeted":false,"id":210621131198173184,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[{"indices":[3,15],"id_str":"178253493","screen_name":"mikalabrags","name":"Mika Labrague","id":178253493}],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"RT @mikalabrags: Bipolar weather \u2601 \u2600","id_str":"210621130703245313","place":null,"retweeted_status":{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"Bipolar weather \u2601 \u2600","id_str":"210619512855343105","place":null,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/ubersocial.com\" rel=\"nofollow\"\u003EUberSocial for BlackBerry\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:29:39 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/503549271\/tumblr_m25lrjIjgT1qb6nmgo1_500.jpg","id_str":"178253493","default_profile_image":false,"statuses_count":13635,"profile_link_color":"06544a","favourites_count":819,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2240536982\/AtRKA77CIAAJRHT_normal.jpg","following":null,"profile_background_color":"373d3a","description":"No fate but what we make","notifications":null,"profile_background_tile":true,"time_zone":"Alaska","profile_sidebar_fill_color":"1c1c21","listed_count":1,"contributors_enabled":false,"geo_enabled":true,"created_at":"Sat Aug 14 07:31:28 +0000 2010","screen_name":"mikalabrags","follow_request_sent":null,"profile_sidebar_border_color":"08080a","protected":false,"url":null,"default_profile":false,"name":"Mika Labrague","is_translator":false,"show_all_inline_media":true,"verified":false,"profile_use_background_image":true,"followers_count":214,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2240536982\/AtRKA77CIAAJRHT_normal.jpg","id":178253493,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/503549271\/tumblr_m25lrjIjgT1qb6nmgo1_500.jpg","utc_offset":-32400,"friends_count":224,"profile_text_color":"352e4d","location":"Mnl"},"retweeted":false,"id":210619512855343105,"coordinates":null,"geo":null},"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/blackberry.com\/twitter\" rel=\"nofollow\"\u003ETwitter for BlackBerry\u00ae\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:05 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/542537222\/534075_10150809727636812_541871811_10087628_844237475_n_large.jpg","id_str":"37200018","default_profile_image":false,"statuses_count":5715,"profile_link_color":"CC3366","favourites_count":46,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2276155427\/photo_201_1_normal.jpg","following":null,"profile_background_color":"dbe9ed","description":"prot\u00e8ge-moi de mes d\u00e9sirs \uf8eb 23107961 \u260d","notifications":null,"profile_background_tile":true,"time_zone":"Singapore","profile_sidebar_fill_color":"ffffff","listed_count":2,"contributors_enabled":false,"geo_enabled":true,"created_at":"Sat May 02 13:55:49 +0000 2009","screen_name":"yoursweetiethea","follow_request_sent":null,"profile_sidebar_border_color":"91f50e","protected":false,"url":"http:\/\/yoursweetiethea.tumblr.com","default_profile":false,"name":"Althea Arellano \u262e","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":306,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2276155427\/photo_201_1_normal.jpg","id":37200018,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/542537222\/534075_10150809727636812_541871811_10087628_844237475_n_large.jpg","utc_offset":28800,"friends_count":297,"profile_text_color":"fa3c6b","location":"Christian's Heart"},"retweeted":false,"id":210621130703245313,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[{"indices":[3,16],"id_str":"230522654","screen_name":"hatena_sugoi","name":"\u300c\u3053\u308c\u306f\u3059\u3054\u3044\u300d","id":230522654}],"urls":[{"display_url":"bit.ly\/MJgpVB","indices":[97,117],"expanded_url":"http:\/\/bit.ly\/MJgpVB","url":"http:\/\/t.co\/9exyeKeN"}],"hashtags":[]},"in_reply_to_screen_name":null,"text":"RT @hatena_sugoi: \uff3b\u901f\u5831\uff3dWindows Azure\u304c\u3064\u3044\u306bIaaS\u6a5f\u80fd\u3092\u767a\u8868\u3002Hyper-V\u4eee\u60f3\u30de\u30b7\u30f3\u304c\u305d\u306e\u307e\u307e\u7a3c\u50cd\u3001\u4eee\u60f3\u30d7\u30e9\u30a4\u30d9\u30fc\u30c8\u30af\u30e9\u30a6\u30c9\u3082\u5b9f\u73fe \uff0d Publickey http:\/\/t.co\/9exyeKeN","id_str":"210621132439687168","place":null,"possibly_sensitive_editable":true,"retweeted_status":{"entities":{"user_mentions":[],"urls":[{"display_url":"bit.ly\/MJgpVB","indices":[79,99],"expanded_url":"http:\/\/bit.ly\/MJgpVB","url":"http:\/\/t.co\/9exyeKeN"}],"hashtags":[]},"in_reply_to_screen_name":null,"text":"\uff3b\u901f\u5831\uff3dWindows Azure\u304c\u3064\u3044\u306bIaaS\u6a5f\u80fd\u3092\u767a\u8868\u3002Hyper-V\u4eee\u60f3\u30de\u30b7\u30f3\u304c\u305d\u306e\u307e\u307e\u7a3c\u50cd\u3001\u4eee\u60f3\u30d7\u30e9\u30a4\u30d9\u30fc\u30c8\u30af\u30e9\u30a6\u30c9\u3082\u5b9f\u73fe \uff0d Publickey http:\/\/t.co\/9exyeKeN","id_str":"210615454006394880","place":null,"possibly_sensitive_editable":true,"in_reply_to_status_id":null,"contributors":null,"retweet_count":2,"favorited":false,"possibly_sensitive":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/twitterfeed.com\" rel=\"nofollow\"\u003Etwitterfeed\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:13:31 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"ja","profile_background_image_url":"http:\/\/a0.twimg.com\/images\/themes\/theme1\/bg.png","id_str":"230522654","default_profile_image":false,"statuses_count":6123,"profile_link_color":"0084B4","favourites_count":0,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/1198697036\/sugoi_normal.gif","following":null,"profile_background_color":"C0DEED","description":"\u306f\u3066\u306a\u30d6\u30c3\u30af\u30de\u30fc\u30af\u306e\u300c\u3053\u308c\u306f\u3059\u3054\u3044\u300d\u30bf\u30b0\u304c\u4ed8\u3044\u305f\u8a18\u4e8b\u3092\u81ea\u52d5\u7684\u306b\u30c4\u30a4\u30fc\u30c8\u3057\u307e\u3059\u3002","notifications":null,"profile_background_tile":false,"time_zone":null,"profile_sidebar_fill_color":"DDEEF6","listed_count":26,"contributors_enabled":false,"geo_enabled":false,"created_at":"Sat Dec 25 21:14:46 +0000 2010","screen_name":"hatena_sugoi","follow_request_sent":null,"profile_sidebar_border_color":"C0DEED","protected":false,"url":null,"default_profile":true,"name":"\u300c\u3053\u308c\u306f\u3059\u3054\u3044\u300d","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":1751,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/1198697036\/sugoi_normal.gif","id":230522654,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/images\/themes\/theme1\/bg.png","utc_offset":null,"friends_count":1407,"profile_text_color":"333333","location":""},"retweeted":false,"id":210615454006394880,"coordinates":null,"geo":null},"in_reply_to_status_id":null,"contributors":null,"retweet_count":2,"favorited":false,"possibly_sensitive":false,"truncated":false,"source":"web","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:05 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"ja","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/439556412\/IMG_0078-2.jpg","id_str":"424091208","default_profile_image":false,"statuses_count":358,"profile_link_color":"00789c","favourites_count":33,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2229043936\/385736_300952569984551_100002094307105_657369_1154995619_n_normal.jpg","following":null,"profile_background_color":"ffffff","description":"Freeskier , DJ (House,Jazz etc.) http:\/\/soundcloud.com\/maeta\/ ","notifications":null,"profile_background_tile":false,"time_zone":"Tokyo","profile_sidebar_fill_color":"DDEEF6","listed_count":0,"contributors_enabled":false,"geo_enabled":false,"created_at":"Tue Nov 29 09:32:34 +0000 2011","screen_name":"maeta_tw","follow_request_sent":null,"profile_sidebar_border_color":"C0DEED","protected":false,"url":"http:\/\/www.facebook.com\/ryuta.mzw","default_profile":false,"name":"\u307e\u3048\u592a","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":76,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2229043936\/385736_300952569984551_100002094307105_657369_1154995619_n_normal.jpg","id":424091208,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/439556412\/IMG_0078-2.jpg","utc_offset":32400,"friends_count":144,"profile_text_color":"333333","location":"Yokohama\/JPN"},"retweeted":false,"id":210621132439687168,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"Loving the weather for tomorrow!","id_str":"210621134411005952","place":{"bounding_box":{"type":"Polygon","coordinates":[[[-117.309797,32.534856],[-116.908259,32.534856],[-116.908259,33.114407],[-117.309797,33.114407]]]},"place_type":"city","country":"United States","attributes":{},"full_name":"San Diego, CA","url":"http:\/\/api.twitter.com\/1\/geo\/id\/a592bd6ceb1319f7.json","name":"San Diego","id":"a592bd6ceb1319f7","country_code":"US"},"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"web","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:06 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/567343447\/7hkd4z088ubrhf00axjn.jpeg","id_str":"90778526","default_profile_image":false,"statuses_count":30072,"profile_link_color":"514f52","favourites_count":60,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2248132461\/image_normal.jpg","following":null,"profile_background_color":"ffffff","description":"Enter my mind, not many make it out.","notifications":null,"profile_background_tile":true,"time_zone":"Alaska","profile_sidebar_fill_color":"000000","listed_count":0,"contributors_enabled":false,"geo_enabled":true,"created_at":"Wed Nov 18 02:14:20 +0000 2009","screen_name":"jslnlvrz","follow_request_sent":null,"profile_sidebar_border_color":"e0b3e0","protected":false,"url":"http:\/\/nileso.tumblr.com\/","default_profile":false,"name":"JXSXLXN \u2020","is_translator":false,"show_all_inline_media":true,"verified":false,"profile_use_background_image":true,"followers_count":1005,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2248132461\/image_normal.jpg","id":90778526,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/567343447\/7hkd4z088ubrhf00axjn.jpeg","utc_offset":-32400,"friends_count":444,"profile_text_color":"828276","location":"San Diego, CA"},"retweeted":false,"id":210621134411005952,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"Surely June is a summer month?! So why is the weather so crap!","id_str":"210621135786741760","place":null,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/ubersocial.com\" rel=\"nofollow\"\u003EUberSocial for BlackBerry\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:06 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/41858423\/nvrocky.br.jpg","id_str":"64683107","default_profile_image":false,"statuses_count":12764,"profile_link_color":"0000ff","favourites_count":6,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2202004627\/339436594_normal.jpg","following":null,"profile_background_color":"000000","description":"LCB Cricket Development Coach in Bolton. Player\/Head Coach of Wigan CC, County Girls Coach and Everton STH in Gwladys Street.  BBM: 28999632","notifications":null,"profile_background_tile":false,"time_zone":"London","profile_sidebar_fill_color":"7DA1B9","listed_count":29,"contributors_enabled":false,"geo_enabled":true,"created_at":"Tue Aug 11 10:52:31 +0000 2009","screen_name":"stick1982","follow_request_sent":null,"profile_sidebar_border_color":"000000","protected":false,"url":"http:\/\/fromoldtraffordtogoodisonpark.blogspot.com\/","default_profile":false,"name":"Chris Highton","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":596,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2202004627\/339436594_normal.jpg","id":64683107,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/41858423\/nvrocky.br.jpg","utc_offset":0,"friends_count":549,"profile_text_color":"000000","location":"Wigan \/ Bolton"},"retweeted":false,"id":210621135786741760,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[],"media":[{"type":"photo","display_url":"pic.twitter.com\/ONuNC8nP","indices":[109,129],"id_str":"210621133844787200","media_url":"http:\/\/p.twimg.com\/AuxGzikCMAA4rp4.jpg","expanded_url":"http:\/\/twitter.com\/EmusGifts\/status\/210621133840592896\/photo\/1","sizes":{"small":{"h":455,"w":340,"resize":"fit"},"large":{"h":1024,"w":765,"resize":"fit"},"thumb":{"h":150,"w":150,"resize":"crop"},"medium":{"h":803,"w":600,"resize":"fit"}},"url":"http:\/\/t.co\/ONuNC8nP","media_url_https":"https:\/\/p.twimg.com\/AuxGzikCMAA4rp4.jpg","id":210621133844787200}],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"We're has the summer gone? Woken up to rain and strong winds. What's the weather like you are waking up too? http:\/\/t.co\/ONuNC8nP","id_str":"210621133840592896","place":null,"possibly_sensitive_editable":true,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"possibly_sensitive":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/twitter.com\/#!\/download\/iphone\" rel=\"nofollow\"\u003ETwitter for iPhone\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:06 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/images\/themes\/theme18\/bg.gif","id_str":"160474696","default_profile_image":false,"statuses_count":1811,"profile_link_color":"038543","favourites_count":57,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2188005135\/emus_jewelery_gifts_small_normal.png","following":null,"profile_background_color":"ACDED6","description":"I am a mother of 3 a who loves making gifts made from upcycled materials","notifications":null,"profile_background_tile":false,"time_zone":"London","profile_sidebar_fill_color":"F6F6F6","listed_count":11,"contributors_enabled":false,"geo_enabled":true,"created_at":"Mon Jun 28 08:00:29 +0000 2010","screen_name":"EmusGifts","follow_request_sent":null,"profile_sidebar_border_color":"EEEEEE","protected":false,"url":"http:\/\/www.emusupcycledgifts.com","default_profile":false,"name":"EmmaNorthcott","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":430,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2188005135\/emus_jewelery_gifts_small_normal.png","id":160474696,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/images\/themes\/theme18\/bg.gif","utc_offset":0,"friends_count":234,"profile_text_color":"333333","location":"Cornwall"},"retweeted":false,"id":210621133840592896,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[{"indices":[0,10],"id_str":"83831112","screen_name":"KSatayBoy","name":"Kenny Kwek","id":83831112}],"urls":[],"hashtags":[]},"in_reply_to_screen_name":"KSatayBoy","text":"@KSatayBoy weather fucking dog sia","id_str":"210621141222559744","place":null,"in_reply_to_status_id":210619253001420800,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/www.tweetdeck.com\" rel=\"nofollow\"\u003ETweetDeck\u003C\/a\u003E","in_reply_to_status_id_str":"210619253001420800","created_at":"Thu Jun 07 06:36:07 +0000 2012","in_reply_to_user_id_str":"83831112","in_reply_to_user_id":83831112,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/images\/themes\/theme1\/bg.png","id_str":"277523269","default_profile_image":false,"statuses_count":18911,"profile_link_color":"12e675","favourites_count":106,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2248303436\/image_normal.jpg","following":null,"profile_background_color":"ededed","description":"harap berdiri di belakang garisan kuning","notifications":null,"profile_background_tile":false,"time_zone":"Singapore","profile_sidebar_fill_color":"DDEEF6","listed_count":0,"contributors_enabled":false,"geo_enabled":true,"created_at":"Tue Apr 05 14:57:27 +0000 2011","screen_name":"plantsgrow","follow_request_sent":null,"profile_sidebar_border_color":"C0DEED","protected":false,"url":"http:\/\/www.formspring.com\/plantsgrow","default_profile":false,"name":"Jonathan \ue518","is_translator":false,"show_all_inline_media":true,"verified":false,"profile_use_background_image":false,"followers_count":297,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2248303436\/image_normal.jpg","id":277523269,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/images\/themes\/theme1\/bg.png","utc_offset":28800,"friends_count":210,"profile_text_color":"333333","location":"Everywhere and nowhere ."},"retweeted":false,"id":210621141222559744,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"Noooooo,Cape Town weather pisses me off nxa 100% chance of rain?? Iryt ? I dnt think so \u2602\u2639","id_str":"210621141499396096","place":null,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/ubersocial.com\" rel=\"nofollow\"\u003EUberSocial for BlackBerry\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:07 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/images\/themes\/theme1\/bg.png","id_str":"164305958","default_profile_image":false,"statuses_count":189,"profile_link_color":"0084B4","favourites_count":1,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2197197149\/_3_3Poz_3_3_E2_84_A2_E2_80_8E_E2_80_8B_E2_80_8B_C2_AE_normal.jpg","following":null,"profile_background_color":"C0DEED","description":"Young and Sexy","notifications":null,"profile_background_tile":false,"time_zone":"Greenland","profile_sidebar_fill_color":"DDEEF6","listed_count":0,"contributors_enabled":false,"geo_enabled":false,"created_at":"Thu Jul 08 15:06:24 +0000 2010","screen_name":"Mapozzz","follow_request_sent":null,"profile_sidebar_border_color":"C0DEED","protected":false,"url":null,"default_profile":true,"name":"Pozisa Koyana","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":43,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2197197149\/_3_3Poz_3_3_E2_84_A2_E2_80_8E_E2_80_8B_E2_80_8B_C2_AE_normal.jpg","id":164305958,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/images\/themes\/theme1\/bg.png","utc_offset":-10800,"friends_count":69,"profile_text_color":"333333","location":"Cape town"},"retweeted":false,"id":210621141499396096,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"Competing in this weather will be horrendous","id_str":"210621147040063488","place":null,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/twitter.com\/#!\/download\/iphone\" rel=\"nofollow\"\u003ETwitter for iPhone\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:09 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/451937829\/tumblr_m12c6rogKY1qadqceo1_500.jpg","id_str":"436111209","default_profile_image":false,"statuses_count":10403,"profile_link_color":"990000","favourites_count":64,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2284922919\/image_normal.jpg","following":null,"profile_background_color":"EBEBEB","description":"fuck it ","notifications":null,"profile_background_tile":true,"time_zone":null,"profile_sidebar_fill_color":"F3F3F3","listed_count":0,"contributors_enabled":false,"geo_enabled":true,"created_at":"Tue Dec 13 20:13:18 +0000 2011","screen_name":"LydiaCrouch","follow_request_sent":null,"profile_sidebar_border_color":"DFDFDF","protected":false,"url":null,"default_profile":false,"name":"lyds\u263a","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":271,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2284922919\/image_normal.jpg","id":436111209,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/451937829\/tumblr_m12c6rogKY1qadqceo1_500.jpg","utc_offset":null,"friends_count":194,"profile_text_color":"333333","location":"Leicester"},"retweeted":false,"id":210621147040063488,"coordinates":null,"geo":null},
{"entities":{"user_mentions":[],"urls":[],"hashtags":[]},"in_reply_to_screen_name":null,"text":"But seriously tho, why did this arctic weather pick today to make an appearance?! :(","id_str":"210621147228807168","place":null,"in_reply_to_status_id":null,"contributors":null,"retweet_count":0,"favorited":false,"truncated":false,"source":"\u003Ca href=\"http:\/\/ubersocial.com\" rel=\"nofollow\"\u003EUberSocial for BlackBerry\u003C\/a\u003E","in_reply_to_status_id_str":null,"created_at":"Thu Jun 07 06:36:09 +0000 2012","in_reply_to_user_id_str":null,"in_reply_to_user_id":null,"user":{"lang":"en","profile_background_image_url":"http:\/\/a0.twimg.com\/profile_background_images\/309207105\/David-Villa-smooches-a-dolphin-500x333.jpg","id_str":"174957097","default_profile_image":false,"statuses_count":11799,"profile_link_color":"B40B43","favourites_count":480,"profile_image_url_https":"https:\/\/si0.twimg.com\/profile_images\/2271591297\/340811827_normal.jpg","following":null,"profile_background_color":"FF6699","description":"Footballista, Fashionista and Musicista :)","notifications":null,"profile_background_tile":true,"time_zone":"Greenland","profile_sidebar_fill_color":"E5507E","listed_count":2,"contributors_enabled":false,"geo_enabled":false,"created_at":"Thu Aug 05 07:12:19 +0000 2010","screen_name":"LatinaJambelina","follow_request_sent":null,"profile_sidebar_border_color":"CC3366","protected":false,"url":null,"default_profile":false,"name":"Jamie-Leigh ","is_translator":false,"show_all_inline_media":false,"verified":false,"profile_use_background_image":true,"followers_count":168,"profile_image_url":"http:\/\/a0.twimg.com\/profile_images\/2271591297\/340811827_normal.jpg","id":174957097,"profile_background_image_url_https":"https:\/\/si0.twimg.com\/profile_background_images\/309207105\/David-Villa-smooches-a-dolphin-500x333.jpg","utc_offset":-10800,"friends_count":92,"profile_text_color":"362720","location":"South Africa"},"retweeted":false,"id":210621147228807168,"coordinates":null,"geo":null}]"""


@pytest.fixture
def jsonschema():
    """Returns a JSON schema for the Twitter data."""

    return {
    "$schema": "http://json-schema.org/schema#",
    "type": "object",
    "properties": {
        "entities": {
            "type": "object",
            "properties": {
                "user_mentions": {
                    "type": "array",
                    "items": [
                        {
                            "type": "object",
                            "properties": {
                                "indices": {
                                    "type": "array",
                                    "items": [{"type": "integer"}, {"type": "integer"}],
                                },
                                "id_str": {"type": "string"},
                                "screen_name": {"type": "string"},
                                "name": {"type": "string"},
                                "id": {"type": "integer"},
                            },
                            "required": [
                                "id",
                                "id_str",
                                "indices",
                                "name",
                                "screen_name",
                            ],
                            "title": "user_mentions",
                        }
                    ],
                },
                "urls": {
                    "type": "array",
                    "items": [
                        {
                            "type": "object",
                            "properties": {
                                "display_url": {"type": "string"},
                                "indices": {
                                    "type": "array",
                                    "items": [{"type": "integer"}, {"type": "integer"}],
                                },
                                "expanded_url": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": [
                                "display_url",
                                "expanded_url",
                                "indices",
                                "url",
                            ],
                            "title": "urls",
                        }
                    ],
                },
                "media": {
                    "type": "array",
                    "items": [
                        {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "display_url": {"type": "string"},
                                "indices": {
                                    "type": "array",
                                    "items": [{"type": "integer"}, {"type": "integer"}],
                                },
                                "id_str": {"type": "string"},
                                "media_url": {"type": "string"},
                                "expanded_url": {"type": "string"},
                                "sizes": {
                                    "type": "object",
                                    "properties": {
                                        "small": {
                                            "type": "object",
                                            "properties": {
                                                "h": {"type": "integer"},
                                                "w": {"type": "integer"},
                                                "resize": {"type": "string"},
                                            },
                                            "required": ["h", "resize", "w"],
                                            "title": "small",
                                        },
                                        "large": {
                                            "type": "object",
                                            "properties": {
                                                "h": {"type": "integer"},
                                                "w": {"type": "integer"},
                                                "resize": {"type": "string"},
                                            },
                                            "required": ["h", "resize", "w"],
                                            "title": "large",
                                        },
                                        "thumb": {
                                            "type": "object",
                                            "properties": {
                                                "h": {"type": "integer"},
                                                "w": {"type": "integer"},
                                                "resize": {"type": "string"},
                                            },
                                            "required": ["h", "resize", "w"],
                                            "title": "thumb",
                                        },
                                        "medium": {
                                            "type": "object",
                                            "properties": {
                                                "h": {"type": "integer"},
                                                "w": {"type": "integer"},
                                                "resize": {"type": "string"},
                                            },
                                            "required": ["h", "resize", "w"],
                                            "title": "medium",
                                        },
                                    },
                                    "required": ["large", "medium", "small", "thumb"],
                                    "title": "sizes",
                                },
                                "url": {"type": "string"},
                                "media_url_https": {"type": "string"},
                                "id": {"type": "integer"},
                            },
                            "required": [
                                "display_url",
                                "expanded_url",
                                "id",
                                "id_str",
                                "indices",
                                "media_url",
                                "media_url_https",
                                "sizes",
                                "type",
                                "url",
                            ],
                            "title": "media",
                        }
                    ],
                },
            },
            "required": ["urls", "user_mentions"],
            "title": "entities",
        },
        "in_reply_to_screen_name": {"type": ["null", "string"]},
        "text": {"type": "string"},
        "id_str": {"type": "string"},
        "place": {
            "type": "object",
            "properties": {
                "bounding_box": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "coordinates": {
                            "type": "array",
                            "items": [
                                {
                                    "type": "array",
                                    "items": [
                                        {
                                            "type": "array",
                                            "items": [
                                                {"type": "number"},
                                                {"type": "number"},
                                            ],
                                        },
                                        {
                                            "type": "array",
                                            "items": [
                                                {"type": "number"},
                                                {"type": "number"},
                                            ],
                                        },
                                        {
                                            "type": "array",
                                            "items": [
                                                {"type": "number"},
                                                {"type": "number"},
                                            ],
                                        },
                                        {
                                            "type": "array",
                                            "items": [
                                                {"type": "number"},
                                                {"type": "number"},
                                            ],
                                        },
                                    ],
                                }
                            ],
                        },
                    },
                    "required": ["coordinates", "type"],
                    "title": "bounding_box",
                },
                "place_type": {"type": "string"},
                "country": {"type": "string"},
                "attributes": {"type": "object", "title": "attributes"},
                "full_name": {"type": "string"},
                "url": {"type": "string"},
                "name": {"type": "string"},
                "id": {"type": "string"},
                "country_code": {"type": "string"},
            },
            "required": [
                "attributes",
                "bounding_box",
                "country",
                "country_code",
                "full_name",
                "id",
                "name",
                "place_type",
                "url",
            ],
            "title": "place",
        },
        "in_reply_to_status_id": {"type": ["integer", "null"]},
        "retweet_count": {"type": "integer"},
        "favorited": {"type": "boolean"},
        "truncated": {"type": "boolean"},
        "source": {"type": "string"},
        "in_reply_to_status_id_str": {"type": ["null", "string"]},
        "created_at": {"type": "string"},
        "in_reply_to_user_id_str": {"type": ["null", "string"]},
        "in_reply_to_user_id": {"type": ["integer", "null"]},
        "user": {
            "type": "object",
            "properties": {
                "lang": {"type": "string"},
                "profile_background_image_url": {"type": "string"},
                "id_str": {"type": "string"},
                "default_profile_image": {"type": "boolean"},
                "statuses_count": {"type": "integer"},
                "profile_link_color": {"type": "string"},
                "favourites_count": {"type": "integer"},
                "profile_image_url_https": {"type": "string"},
                "profile_background_color": {"type": "string"},
                "description": {"type": "string"},
                "profile_background_tile": {"type": "boolean"},
                "time_zone": {"type": ["null", "string"]},
                "profile_sidebar_fill_color": {"type": "string"},
                "listed_count": {"type": "integer"},
                "contributors_enabled": {"type": "boolean"},
                "geo_enabled": {"type": "boolean"},
                "created_at": {"type": "string"},
                "screen_name": {"type": "string"},
                "profile_sidebar_border_color": {"type": "string"},
                "protected": {"type": "boolean"},
                "url": {"type": ["null", "string"]},
                "default_profile": {"type": "boolean"},
                "name": {"type": "string"},
                "is_translator": {"type": "boolean"},
                "show_all_inline_media": {"type": "boolean"},
                "verified": {"type": "boolean"},
                "profile_use_background_image": {"type": "boolean"},
                "followers_count": {"type": "integer"},
                "profile_image_url": {"type": "string"},
                "id": {"type": "integer"},
                "profile_background_image_url_https": {"type": "string"},
                "utc_offset": {"type": ["integer", "null"]},
                "friends_count": {"type": "integer"},
                "profile_text_color": {"type": "string"},
                "location": {"type": "string"},
            },
            "required": [
                "contributors_enabled",
                "created_at",
                "default_profile",
                "default_profile_image",
                "description",
                "favourites_count",
                "followers_count",
                "friends_count",
                "geo_enabled",
                "id",
                "id_str",
                "is_translator",
                "lang",
                "listed_count",
                "location",
                "name",
                "profile_background_color",
                "profile_background_image_url",
                "profile_background_image_url_https",
                "profile_background_tile",
                "profile_image_url",
                "profile_image_url_https",
                "profile_link_color",
                "profile_sidebar_border_color",
                "profile_sidebar_fill_color",
                "profile_text_color",
                "profile_use_background_image",
                "protected",
                "screen_name",
                "show_all_inline_media",
                "statuses_count",
                "time_zone",
                "url",
                "utc_offset",
                "verified",
            ],
            "title": "user",
        },
        "retweeted": {"type": "boolean"},
        "id": {"type": "integer"},
        "retweeted_status": {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "display_url": {"type": "string"},
                                        "indices": {
                                            "type": "array",
                                            "items": [
                                                {"type": "integer"},
                                                {"type": "integer"},
                                            ],
                                        },
                                        "expanded_url": {"type": "string"},
                                        "url": {"type": "string"},
                                    },
                                    "required": [
                                        "display_url",
                                        "expanded_url",
                                        "indices",
                                        "url",
                                    ],
                                    "title": "urls",
                                }
                            ],
                        }
                    },
                    "required": ["urls"],
                    "title": "entities",
                },
                "text": {"type": "string"},
                "id_str": {"type": "string"},
                "retweet_count": {"type": "integer"},
                "favorited": {"type": "boolean"},
                "truncated": {"type": "boolean"},
                "source": {"type": "string"},
                "created_at": {"type": "string"},
                "user": {
                    "type": "object",
                    "properties": {
                        "lang": {"type": "string"},
                        "profile_background_image_url": {"type": "string"},
                        "id_str": {"type": "string"},
                        "default_profile_image": {"type": "boolean"},
                        "statuses_count": {"type": "integer"},
                        "profile_link_color": {"type": "string"},
                        "favourites_count": {"type": "integer"},
                        "profile_image_url_https": {"type": "string"},
                        "profile_background_color": {"type": "string"},
                        "description": {"type": "string"},
                        "profile_background_tile": {"type": "boolean"},
                        "time_zone": {"type": ["null", "string"]},
                        "profile_sidebar_fill_color": {"type": "string"},
                        "listed_count": {"type": "integer"},
                        "contributors_enabled": {"type": "boolean"},
                        "geo_enabled": {"type": "boolean"},
                        "created_at": {"type": "string"},
                        "screen_name": {"type": "string"},
                        "profile_sidebar_border_color": {"type": "string"},
                        "protected": {"type": "boolean"},
                        "default_profile": {"type": "boolean"},
                        "name": {"type": "string"},
                        "is_translator": {"type": "boolean"},
                        "show_all_inline_media": {"type": "boolean"},
                        "verified": {"type": "boolean"},
                        "profile_use_background_image": {"type": "boolean"},
                        "followers_count": {"type": "integer"},
                        "profile_image_url": {"type": "string"},
                        "id": {"type": "integer"},
                        "profile_background_image_url_https": {"type": "string"},
                        "utc_offset": {"type": ["integer", "null"]},
                        "friends_count": {"type": "integer"},
                        "profile_text_color": {"type": "string"},
                        "location": {"type": "string"},
                    },
                    "required": [
                        "contributors_enabled",
                        "created_at",
                        "default_profile",
                        "default_profile_image",
                        "description",
                        "favourites_count",
                        "followers_count",
                        "friends_count",
                        "geo_enabled",
                        "id",
                        "id_str",
                        "is_translator",
                        "lang",
                        "listed_count",
                        "location",
                        "name",
                        "profile_background_color",
                        "profile_background_image_url",
                        "profile_background_image_url_https",
                        "profile_background_tile",
                        "profile_image_url",
                        "profile_image_url_https",
                        "profile_link_color",
                        "profile_sidebar_border_color",
                        "profile_sidebar_fill_color",
                        "profile_text_color",
                        "profile_use_background_image",
                        "protected",
                        "screen_name",
                        "show_all_inline_media",
                        "statuses_count",
                        "time_zone",
                        "utc_offset",
                        "verified",
                    ],
                    "title": "user",
                },
                "retweeted": {"type": "boolean"},
                "id": {"type": "integer"},
                "possibly_sensitive_editable": {"type": "boolean"},
                "possibly_sensitive": {"type": "boolean"},
            },
            "required": [
                "created_at",
                "entities",
                "favorited",
                "id",
                "id_str",
                "retweet_count",
                "retweeted",
                "source",
                "text",
                "truncated",
                "user",
            ],
            "title": "retweeted_status",
        },
        "possibly_sensitive_editable": {"type": "boolean"},
        "possibly_sensitive": {"type": "boolean"},
    },
    "required": [
        "created_at",
        "entities",
        "favorited",
        "id",
        "id_str",
        "in_reply_to_screen_name",
        "in_reply_to_status_id",
        "in_reply_to_status_id_str",
        "in_reply_to_user_id",
        "in_reply_to_user_id_str",
        "place",
        "retweet_count",
        "retweeted",
        "source",
        "text",
        "truncated",
        "user",
    ],
    "title": "nlp4all",
}
