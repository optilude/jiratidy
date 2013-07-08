"""Print comments beloning to a given group

Installation:

  1) Install Python 2.7
  2) Install pip (possibly in a virtualenv)
  3) $ pip install requests

Usage:

  $ python comments.py --url <JIRA URL> --username=<username> --group=<group name> --project=<project key>

e.g.:

  $ python comments.py --url https://test.jira.com --username=testuser --group=MyGroup --project=ABC
"""

from __future__ import print_function

import json
import urlparse
import argparse
import getpass
import requests

API_ROOT = '/rest/api/2'


class JIRA(object):
    """Helper class for executing JIRA operations
    """

    def __init__(self, username, password, base_url):
        self.username = username
        self.password = password
        self.base_url = base_url

    def get(self, rest_url, params={}):
        """Make a GET web service call to rest_url and return the results as JSON.
        """
        url = urlparse.urljoin(self.base_url, API_ROOT) + rest_url
        r = requests.get(url, params=params, auth=(self.username, self.password))

        if r.status_code != 200:
            print("Error", r.status_code, "getting from", r.url)
            if r.status_code == 403:
                print(r.headers)
            print(r.text)
            return None

        return r.json()

    def post(self, rest_url, data={}):
        """Make a POST web service call to rest_url and return the results as JSON.
        """
        url = urlparse.urljoin(self.base_url, API_ROOT) + rest_url
        headers = {'content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers, auth=(self.username, self.password))

        if r.status_code != 200:
            print("Error", r.status_code, "posting to", r.url, "with body", r.request.body)
            if r.status_code == 403:
                print(r.headers)
            print(r.text)
            return None

        return r.json()

    def search(self, jql, startAt=0, maxResults=1000, fields="*navigable"):
        return self.get('/search', {
            'jql': jql,
            'fields': fields,
            'startAt': startAt,
            'maxResults': maxResults,
        })

    def fetch_issue(self, issue_key):
        return self.get('/issue/' + issue_key)

# One-off script


def print_comments_specific_to_group():
    parser = argparse.ArgumentParser(description='Show comments on issues visible to a specific group only')
    parser.add_argument('--url', dest='url', help='JIRA instance URL')
    parser.add_argument('--username', dest='username', help='JIRA user name')
    parser.add_argument('--group', dest='group', help='group name to check for')
    parser.add_argument('--project', dest='project', help='project key')

    password = getpass.getpass("Password:")
    args = parser.parse_args()

    api = JIRA(args.username, password, args.url)

    start_at = 0
    total_results = None

    while True:
        num_printed = 0
        results = api.search('project=%s' % args.project, startAt=start_at, maxResults=1000, fields="summary,comment")
        total_results = results['total']
        for issue in results['issues']:
            num_printed += 1

            for comment in issue['fields'].get('comment', {}).get('comments', []):
                if 'visibility' in comment:
                    if comment['visibility']['type'] == 'group' and comment['visibility']['value'].lower() == args.group.lower():
                        print("")
                        print("*", issue['key'], issue['fields']['summary'].encode('utf-8'))
                        print("")
                        print("Comment", comment['id'])
                        print("----- 8< ----")
                        print(comment['body'].encode('utf-8'))
                        print("----- 8< ----")
                        print("")

            num_printed += 1
        if start_at + num_printed < total_results:
            start_at = start_at + num_printed
        else:
            break

if __name__ == '__main__':
    print_comments_specific_to_group()
