import re

from django.conf import settings
from apps.customizer.models import Configuration
from django.utils.deprecation import MiddlewareMixin

words_re = re.compile( r'\s+' )

group_prefix_re = [
    re.compile( "^.*/django/[^/]+" ),
    re.compile( "^(.*)/[^/]+$" ), # extract module path
    re.compile( ".*" ),           # catch strange entries
]


# This middleware seems to have been unused, so I've commented it out.

# class ProfileMiddleware(object):
#     """
#     Displays hotshot profiling for any view.
#     http://yoursite.com/yourview/?prof
#
#     Add the "prof" key to query string by appending ?prof (or &prof=)
#     and you'll see the profiling results in your browser.
#     It's set up to only be available in django's debug mode, is available for superuser otherwise,
#     but you really shouldn't add this middleware to any production configuration.
#
#     WARNING: It uses hotshot profiler which is not thread safe.
#     """
#     def process_request(self, request):
#         if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
#             self.tmpfile = tempfile.mktemp()
#             self.prof = hotshot.Profile(self.tmpfile)
#
#     def process_view(self, request, callback, callback_args, callback_kwargs):
#         if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
#             return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)
#
#     def get_group(self, file):
#         for g in group_prefix_re:
#             name = g.findall( file )
#             if name:
#                 return name[0]
#
#     def get_summary(self, results_dict, sum):
#         list = [ (item[1], item[0]) for item in list(results_dict.items()) ]
#         list.sort( reverse = True )
#         list = list[:40]
#
#         res = "      tottime\n"
#         for item in list:
#             res += "%4.1f%% %7.3f %s\n" % ( 100*item[0]/sum if sum else 0, item[0], item[1] )
#
#         return res
#
#     def summary_for_files(self, stats_str):
#         stats_str = stats_str.split("\n")[5:]
#
#         mystats = {}
#         mygroups = {}
#
#         sum = 0
#
#         for s in stats_str:
#             fields = words_re.split(s);
#             if len(fields) == 7:
#                 time = float(fields[2])
#                 sum += time
#                 file = fields[6].split(":")[0]
#
#                 if not file in mystats:
#                     mystats[file] = 0
#                 mystats[file] += time
#
#                 group = self.get_group(file)
#                 if not group in mygroups:
#                     mygroups[ group ] = 0
#                 mygroups[ group ] += time
#
#         return "<pre>" + \
#                " ---- By file ----\n\n" + self.get_summary(mystats,sum) + "\n" + \
#                " ---- By group ---\n\n" + self.get_summary(mygroups,sum) + \
#                "</pre>"
#
#     def process_response(self, request, response):
#         if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
#             self.prof.close()
#
#             out = io.StringIO()
#             old_stdout = sys.stdout
#             sys.stdout = out
#
#             stats = hotshot.stats.load(self.tmpfile)
#             stats.sort_stats('time', 'calls')
#             stats.print_stats()
#
#             sys.stdout = old_stdout
#             stats_str = out.getvalue()
#
#             if response and response.content and stats_str:
#                 response.content = "<pre>" + stats_str + "</pre>"
#
#             response.content = "\n".join(response.content.split("\n")[:40])
#
#             response.content += self.summary_for_files(stats_str)
#
#             os.unlink(self.tmpfile)
#
#         return response


class SingleCompetitionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not settings.SINGLE_COMPETITION_VIEW_PK or not settings.CUSTOM_HEADER_LOGO:
            # Try and get from database if we don't have competition set in ENV vars
            config, created = Configuration.objects.get_or_create(pk=1)

            if config.only_competition:
                settings.SINGLE_COMPETITION_VIEW_PK = config.only_competition.pk

            if config.header_logo:
                settings.CUSTOM_HEADER_LOGO = config.header_logo.url
