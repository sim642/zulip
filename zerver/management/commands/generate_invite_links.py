from __future__ import absolute_import

from optparse import make_option

from django.core.management.base import BaseCommand
from confirmation.models import Confirmation
from zerver.models import UserProfile, PreregistrationUser, \
    get_user_profile_by_email, get_realm

class Command(BaseCommand):
    help = "Generate activation links for users and print them to stdout."

    option_list = BaseCommand.option_list + (
        make_option('--domain',
                    dest='domain',
                    type='str',
                    help='The realm in which to generate the invites (use for open realms).'),
        make_option('--force',
                    dest='force',
                    action="store_true",
                    default=False,
                    help='Override that the domain is restricted to external users.'),
        )

    def handle(self, *args, **options):
        duplicates = False
        for email in args:
            try:
                get_user_profile_by_email(email)
                print email + ": There is already a user registered with that address."
                duplicates = True
                continue
            except UserProfile.DoesNotExist:
                pass

        if duplicates:
            return

        realm = None
        domain = options["domain"]
        if domain:
            realm = get_realm(domain)
        if not realm:
            print "The realm %s doesn't exist yet, please create it first." % (domain,)
            print "Don't forget default streams!"
            exit(1)

        for email in args:
            if realm:
                if realm.restricted_to_domain and \
                        domain.lower() != email.split("@", 1)[-1].lower() and \
                        not options["force"]:
                    print "You've asked to add an external user (%s) to a closed realm (%s)." % (
                        email, domain)
                    print "Are you sure? To do this, pass --force."
                    exit(1)
                else:
                    prereg_user = PreregistrationUser(email=email, realm=realm)
            else:
                prereg_user = PreregistrationUser(email=email)
            prereg_user.save()
            print email + ": " + Confirmation.objects.get_link_for_object(prereg_user)

