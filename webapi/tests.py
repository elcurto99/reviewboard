import unittest

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import simplejson
from djblets.util.testing import TagTest

import reviewboard.webapi.json as webapi
from reviewboard.reviews.models import Group, ReviewRequest, \
                                       ReviewRequestDraft, Review, \
                                       Comment, ScreenshotComment
from reviewboard.scmtools.models import Repository


class WebAPITests(TestCase):
    """Testing the webapi support."""
    fixtures = ['test_users', 'test_reviewrequests', 'test_scmtools']

    def setUp(self):
        self.client.login(username="grumpy", password="grumpy")
        self.user = User.objects.get(username="grumpy")

    def tearDown(self):
        self.client.logout()

    def apiGet(self, path, query={}):
        response = self.client.get("/api/json/%s/" % path, query)
        self.assertEqual(response.status_code, 200)
        rsp = simplejson.loads(response.content)
        return rsp

    def apiPost(self, path, query={}):
        print "Posting to /api/json/%s/" % path
        response = self.client.post("/api/json/%s/" % path, query)
        self.assertEqual(response.status_code, 200)
        rsp = simplejson.loads(response.content)
        return rsp

    def testRepositoryList(self):
        """Testing the repositories API"""
        rsp = self.apiGet("repositories")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['repositories']), Repository.objects.count())

    def testUserList(self):
        """Testing the users API"""
        rsp = self.apiGet("users")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['users']), User.objects.count())

    def testUserListQuery(self):
        """Testing the users API with custom query"""
        rsp = self.apiGet("users", {'query': 'gru'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['users']), 1) # grumpy

    def testGroupList(self):
        """Testing the groups API"""
        rsp = self.apiGet("groups")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['groups']), Group.objects.count())

    def testGroupListQuery(self):
        """Testing the groups API with custom query"""
        rsp = self.apiGet("groups", {'query': 'dev'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['groups']), 1) #devgroup

    def testGroupStar(self):
        """Testing the groups/star API"""
        rsp = self.apiGet("groups/devgroup/star")
        self.assertEqual(rsp['stat'], 'ok')
        self.assert_(Group.objects.get(name="devgroup") in
                     self.user.get_profile().starred_groups.all())

    def testGroupStarDoesNotExist(self):
        """Testing the groups/star API with Does Not Exist error"""
        rsp = self.apiGet("groups/invalidgroup/star")
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.DOES_NOT_EXIST.code)

    def testGroupUnstar(self):
        """Testing the groups/unstar API"""
        # First, star it.
        self.testGroupStar()

        rsp = self.apiGet("groups/devgroup/unstar")
        self.assertEqual(rsp['stat'], 'ok')
        self.assert_(Group.objects.get(name="devgroup") not in
                     self.user.get_profile().starred_groups.all())

    def testGroupUnstarDoesNotExist(self):
        """Testing the groups/unstar API with Does Not Exist error"""
        rsp = self.apiGet("groups/invalidgroup/unstar")
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.DOES_NOT_EXIST.code)

    def testReviewRequestList(self):
        """Testing the reviewrequests/all API"""
        rsp = self.apiGet("reviewrequests/all")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.public().count())

    def testReviewRequestListWithStatus(self):
        """Testing the reviewrequests/all API with custom status"""
        rsp = self.apiGet("reviewrequests/all", {'status': 'submitted'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.public(status='S').count())

        rsp = self.apiGet("reviewrequests/all", {'status': 'discarded'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.public(status='D').count())

        rsp = self.apiGet("reviewrequests/all", {'status': 'all'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.public(status=None).count())

    def testReviewRequestListCount(self):
        """Testing the reviewrequests/all/count API"""
        rsp = self.apiGet("reviewrequests/all/count")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['count'], ReviewRequest.objects.public().count())

    def testReviewRequestsToGroup(self):
        """Testing the reviewrequests/to/group API"""
        rsp = self.apiGet("reviewrequests/to/group/devgroup")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.to_group("devgroup").count())

    def testReviewRequestsToGroupWithStatus(self):
        """Testing the reviewrequests/to/group API with custom status"""
        rsp = self.apiGet("reviewrequests/to/group/devgroup",
                          {'status': 'submitted'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
            ReviewRequest.objects.to_group("devgroup", status='S').count())

        rsp = self.apiGet("reviewrequests/to/group/devgroup",
                          {'status': 'discarded'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
            ReviewRequest.objects.to_group("devgroup", status='D').count())

    def testReviewRequestsToGroupCount(self):
        """Testing the reviewrequests/to/group/count API"""
        rsp = self.apiGet("reviewrequests/to/group/devgroup/count")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['count'],
                         ReviewRequest.objects.to_group("devgroup").count())

    def testReviewRequestsToUser(self):
        """Testing the reviewrequests/to/user API"""
        rsp = self.apiGet("reviewrequests/to/user/grumpy")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.to_user("grumpy").count())

    def testReviewRequestsToUserWithStatus(self):
        """Testing the reviewrequests/to/user API with custom status"""
        rsp = self.apiGet("reviewrequests/to/user/grumpy",
                          {'status': 'submitted'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
            ReviewRequest.objects.to_user("grumpy", status='S').count())

        rsp = self.apiGet("reviewrequests/to/user/grumpy",
                          {'status': 'discarded'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
            ReviewRequest.objects.to_user("grumpy", status='D').count())

    def testReviewRequestsToUserCount(self):
        """Testing the reviewrequests/to/user/count API"""
        rsp = self.apiGet("reviewrequests/to/user/grumpy/count")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['count'],
                         ReviewRequest.objects.to_user("grumpy").count())

    def testReviewRequestsFromUser(self):
        """Testing the reviewrequests/from/user API"""
        rsp = self.apiGet("reviewrequests/from/user/grumpy")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
                         ReviewRequest.objects.from_user("grumpy").count())

    def testReviewRequestsFromUserWithStatus(self):
        """Testing the reviewrequests/from/user API with custom status"""
        rsp = self.apiGet("reviewrequests/from/user/grumpy",
                          {'status': 'submitted'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
            ReviewRequest.objects.from_user("grumpy", status='S').count())

        rsp = self.apiGet("reviewrequests/from/user/grumpy",
                          {'status': 'discarded'})
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['review_requests']),
            ReviewRequest.objects.from_user("grumpy", status='D').count())

    def testReviewRequestsFromUserCount(self):
        """Testing the reviewrequests/from/user/count API"""
        rsp = self.apiGet("reviewrequests/from/user/grumpy/count")
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['count'],
                         ReviewRequest.objects.from_user("grumpy").count())

    def testNewReviewRequest(self):
        """Testing the reviewrequests/new API"""
        repository = Repository.objects.all()[0]
        rsp = self.apiPost("reviewrequests/new", {
            'repository_path': repository.path,
        })
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['review_request']['repository']['id'],
                         repository.id)

        # See if we can fetch this.
        ReviewRequest.objects.get(pk=rsp['review_request']['id'])

    def testReviewRequest(self):
        """Testing the reviewrequests/<id> API"""
        review_request = ReviewRequest.objects.public()[0]
        rsp = self.apiGet("reviewrequests/%s" % review_request.id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['review_request']['id'], review_request.id)
        self.assertEqual(rsp['review_request']['summary'],
                         review_request.summary)

    def testReviewRequestPermissionDenied(self):
        """Testing the reviewrequests/<id> API with Permission Denied error"""
        review_request = ReviewRequest.objects.filter(public=False).\
            exclude(submitter=self.user)[0]
        rsp = self.apiGet("reviewrequests/%s" % review_request.id)
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.PERMISSION_DENIED.code)

    def testReviewRequestByChangenum(self):
        """Testing the reviewrequests/repository/changenum API"""
        review_request = \
            ReviewRequest.objects.filter(changenum__isnull=False)[0]
        rsp = self.apiGet("reviewrequests/repository/%s/changenum/%s" %
                          (review_request.repository.id,
                           review_request.changenum))
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['review_request']['id'], review_request.id)
        self.assertEqual(rsp['review_request']['summary'],
                         review_request.summary)
        self.assertEqual(rsp['review_request']['changenum'],
                         review_request.changenum)

    def testReviewRequestStar(self):
        """Testing the reviewrequests/star API"""
        review_request = ReviewRequest.objects.public()[0]
        rsp = self.apiGet("reviewrequests/%s/star" % review_request.id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assert_(review_request in
                     self.user.get_profile().starred_review_requests.all())

    def testReviewRequestStarDoesNotExist(self):
        """Testing the reviewrequests/star API with Does Not Exist error"""
        rsp = self.apiGet("reviewrequests/999/star")
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.DOES_NOT_EXIST.code)

    def testReviewRequestUnstar(self):
        """Testing the reviewrequests/unstar API"""
        # First, star it.
        self.testReviewRequestStar()

        review_request = ReviewRequest.objects.public()[0]
        rsp = self.apiGet("reviewrequests/%s/unstar" % review_request.id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assert_(review_request not in
                     self.user.get_profile().starred_review_requests.all())

    def testReviewRequestUnstarWithDoesNotExist(self):
        """Testing the reviewrequests/unstar API with Does Not Exist error"""
        rsp = self.apiGet("reviewrequests/999/unstar")
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.DOES_NOT_EXIST.code)

    def testReviewRequestDelete(self):
        """Testing the reviewrequests/delete API"""
        self.user.user_permissions.add(
            Permission.objects.get(codename='delete_reviewrequest'))
        self.user.save()
        self.assert_(self.user.has_perm('reviews.delete_reviewrequest'))

        review_request_id = \
            ReviewRequest.objects.filter(submitter=self.user)[0].id
        rsp = self.apiGet("reviewrequests/%s/delete" % review_request_id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertRaises(ReviewRequest.DoesNotExist,
                          ReviewRequest.objects.get, pk=review_request_id)

    def testReviewRequestDeletePermissionDenied(self):
        """Testing the reviewrequests/delete API with Permission Denied error"""
        review_request_id = \
            ReviewRequest.objects.exclude(submitter=self.user)[0].id
        rsp = self.apiGet("reviewrequests/%s/delete" % review_request_id)
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.PERMISSION_DENIED.code)

    def testReviewRequestDeleteDoesNotExist(self):
        """Testing the reviewrequests/delete API with Does Not Exist error"""
        self.user.user_permissions.add(
            Permission.objects.get(codename='delete_reviewrequest'))
        self.user.save()
        self.assert_(self.user.has_perm('reviews.delete_reviewrequest'))

        rsp = self.apiGet("reviewrequests/999/delete")
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.DOES_NOT_EXIST.code)

    def testReviewRequestDraftSet(self):
        """Testing the reviewrequests/draft/set API"""
        summary = "My Summary"
        description = "My Description"
        testing_done = "My Testing Done"
        branch = "My Branch"
        bugs = ""

        review_request_id = \
            ReviewRequest.objects.filter(submitter=self.user)[0].id
        rsp = self.apiPost("reviewrequests/%s/draft/set" % review_request_id, {
            'summary': summary,
            'description': description,
            'testing_done': testing_done,
            'branch': branch,
            'bugs_closed': bugs,
        })

        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['draft']['summary'], summary)
        self.assertEqual(rsp['draft']['description'], description)
        self.assertEqual(rsp['draft']['testing_done'], testing_done)
        self.assertEqual(rsp['draft']['branch'], branch)
        self.assertEqual(rsp['draft']['bugs_closed'], [])

        draft = ReviewRequestDraft.objects.get(pk=rsp['draft']['id'])
        self.assertEqual(draft.summary, summary)
        self.assertEqual(draft.description, description)
        self.assertEqual(draft.testing_done, testing_done)
        self.assertEqual(draft.branch, branch)
        self.assertEqual(draft.get_bug_list(), [])

    def testReviewRequestDraftSetField(self):
        """Testing the reviewrequests/draft/set/<field> API"""
        bugs_closed = '123,456'
        review_request_id = \
            ReviewRequest.objects.filter(submitter=self.user)[0].id
        rsp = self.apiPost("reviewrequests/%s/draft/set/bugs_closed" %
                           review_request_id, {
            'value': bugs_closed,
        })

        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['bugs_closed'], bugs_closed.split(","))

    def testReviewRequestDraftSetFieldInvalidName(self):
        """Testing the reviewrequests/draft/set/<field> API with invalid name"""
        review_request_id = \
            ReviewRequest.objects.filter(submitter=self.user)[0].id
        rsp = self.apiPost("reviewrequests/%s/draft/set/foobar" %
                           review_request_id, {
            'value': 'foo',
        })

        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.INVALID_ATTRIBUTE.code)
        self.assertEqual(rsp['attribute'], 'foobar')

    def testReviewRequestDraftSave(self):
        """Testing the reviewrequests/draft/save API"""
        # Set some data first.
        self.testReviewRequestDraftSet()

        review_request_id = \
            ReviewRequest.objects.filter(submitter=self.user)[0].id
        rsp = self.apiPost("reviewrequests/%s/draft/save" % review_request_id)

        self.assertEqual(rsp['stat'], 'ok')

        review_request = ReviewRequest.objects.get(pk=review_request_id)
        self.assertEqual(review_request.summary, "My Summary")
        self.assertEqual(review_request.description, "My Description")
        self.assertEqual(review_request.testing_done, "My Testing Done")
        self.assertEqual(review_request.branch, "My Branch")

    def testReviewRequestDraftDiscard(self):
        """Testing the reviewrequests/draft/discard API"""
        review_request = ReviewRequest.objects.filter(submitter=self.user)[0]
        summary = review_request.summary
        description = review_request.description

        # Set some data.
        self.testReviewRequestDraftSet()

        rsp = self.apiPost("reviewrequests/%s/draft/discard" %
                           review_request.id)
        self.assertEqual(rsp['stat'], 'ok')

        review_request = ReviewRequest.objects.get(pk=review_request.id)
        self.assertEqual(review_request.summary, summary)
        self.assertEqual(review_request.description, description)

    def testReviewDraftSave(self):
        """Testing the reviewrequests/reviews/draft/save API"""
        body_top = "My Body Top"
        body_bottom = "My Body Bottom"
        ship_it = True

        # Clear out any reviews on the first review request we find.
        review_request = ReviewRequest.objects.public()[0]
        review_request.review_set = []
        review_request.save()

        rsp = self.apiPost("reviewrequests/%s/reviews/draft/save" %
                           review_request.id, {
            'shipit': ship_it,
            'body_top': body_top,
            'body_bottom': body_bottom,
        })

        reviews = review_request.review_set.filter(user=self.user)
        self.assertEqual(len(reviews), 1)
        review = reviews[0]

        self.assertEqual(review.ship_it, ship_it)
        self.assertEqual(review.body_top, body_top)
        self.assertEqual(review.body_bottom, body_bottom)
        self.assertEqual(review.public, False)

    def testReviewDraftPublish(self):
        """Testing the reviewrequests/reviews/draft/publish API"""
        body_top = "My Body Top"
        body_bottom = "My Body Bottom"
        ship_it = True

        # Clear out any reviews on the first review request we find.
        review_request = ReviewRequest.objects.public()[0]
        review_request.review_set = []
        review_request.save()

        rsp = self.apiPost("reviewrequests/%s/reviews/draft/publish" %
                           review_request.id, {
            'shipit': ship_it,
            'body_top': body_top,
            'body_bottom': body_bottom,
        })

        self.assertEqual(rsp['stat'], 'ok')

        reviews = review_request.review_set.filter(user=self.user)
        self.assertEqual(len(reviews), 1)
        review = reviews[0]

        self.assertEqual(review.ship_it, ship_it)
        self.assertEqual(review.body_top, body_top)
        self.assertEqual(review.body_bottom, body_bottom)
        self.assertEqual(review.public, True)

    def testReviewDraftDelete(self):
        """Testing the reviewrequests/reviews/draft/delete API"""
        # Set up the draft to delete.
        self.testReviewDraftSave()

        review_request = ReviewRequest.objects.public()[0]
        rsp = self.apiPost("reviewrequests/%s/reviews/draft/delete" %
                           review_request.id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(review_request.review_set.count(), 0)

    def testReviewDraftDeleteDoesNotExist(self):
        """Testing the reviewrequests/reviews/draft/delete API with Does Not Exist error"""
        # Set up the draft to delete
        self.testReviewDraftPublish()

        review_request = ReviewRequest.objects.public()[0]
        rsp = self.apiPost("reviewrequests/%s/reviews/draft/delete" %
                           review_request.id)
        self.assertEqual(rsp['stat'], 'fail')
        self.assertEqual(rsp['err']['code'], webapi.DOES_NOT_EXIST.code)

    def testReviewDraftComments(self):
        """Testing the reviewrequests/reviews/draft/comments API"""
        #review_request = \
        #    ReviewRequest.objects.public().filter(review__comments__pk__gt=0)[0]

        #rsp = self.apiGet("reviewrequests/%s/reviews/draft/comments" %
        #                  review_request.id)
        #self.assertEqual(rsp['stat'], 'ok')
        #self.assertEqual(len(rsp['comments'], 
        pass

    def testReviewsList(self):
        """Testing the reviewrequests/reviews API"""
        review_request = Review.objects.all()[0].review_request
        rsp = self.apiGet("reviewrequests/%s/reviews" % review_request.id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['reviews']), review_request.review_set.count())

    def testReviewsListCount(self):
        """Testing the reviewrequests/reviews/count API"""
        review_request = Review.objects.all()[0].review_request
        rsp = self.apiGet("reviewrequests/%s/reviews/count" %
                          review_request.id)
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['reviews'], review_request.review_set.count())

    def testReviewCommentsList(self):
        """Testing the reviewrequests/reviews/comments API"""
        review = Review.objects.filter(comments__pk__gt=0)[0]
        review_request = review.review_request

        rsp = self.apiGet("reviewrequests/%s/reviews/%s/comments" %
                          (review_request.id, review.id))
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(len(rsp['comments']), review.comments.count())

    def testReviewCommentsCount(self):
        """Testing the reviewrequests/reviews/comments/count API"""
        review = Review.objects.filter(comments__pk__gt=0)[0]
        review_request = review.review_request

        rsp = self.apiGet("reviewrequests/%s/reviews/%s/comments/count" %
                          (review_request.id, review.id))
        self.assertEqual(rsp['stat'], 'ok')
        self.assertEqual(rsp['count'], review.comments.count())