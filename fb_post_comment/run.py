#!/usr/bin/env python3

import argparse
import re
import sys

import facebook_scrape


def scrape_group_posts(group_id, app_id, app_secret, output_filename):
    facebook_scrape.scrape_posts(group_id, "group", app_id, app_secret, 
                                 output_filename)


def scrape_page_posts(page_id, app_id, app_secret, output_filename):
    facebook_scrape.scrape_posts(page_id, "page", app_id, app_secret, 
                                 output_filename)


def scrape_comments(page_id, app_id, app_secret, input_filename, 
                    output_filename, scrape_author_id):
    facebook_scrape.scrape_comments(page_id, app_id, app_secret, 
                                    input_filename, output_filename, 
                                    scrape_author_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper for *all* " + \
            "posts, reactions, and (optionally) comments on a public " + \
            "Facebook group or page.")

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--group", metavar="Public group ID", type=str, 
            help="The ID of the open/public Facebook group you want to " + \
                    "scrape.")

    group.add_argument("--page", metavar="Public page ID", type=str, 
            help="The ID of the Facebook page you want to scrape.")

    parser.add_argument("--cred", metavar="Credential file", type=str, 
            required=True,
            help="Path to a secret credentials file containing your app " + \
                "ID and app secret. See README.md for the " + \
                "credential file format.")

    parser.add_argument("--posts-output", metavar="Output CSV file for posts", 
            type=str, required=True, 
            help="Path to where you want the output CSV file to be")

    parser.add_argument("--scrape-comments", action="store_true", 
            required=False, help="Scrape comments as well as posts.")

    parser.add_argument("--comments-output", metavar="Output CSV file for " + \
            "comments",
            type=str, required=False,
            help="Path to where you want the output CSV file for comments " + \
                    "to be")

    parser.add_argument("--scrape-author-id", action="store_true", 
            required=False, help="Scrape comment authors' Facebook IDs")

    parser.add_argument("--use-existing-posts-csv", action="store_true", 
            required=False, help="Scrape comments from an existing " + \
            "status/post CSV. Specify it using the --posts-output argument.")

    args = parser.parse_args()

    if args.scrape_comments and args.comments_output is None:
        parser.error("Please specify an output CSV file for comments")

    # get credentials
    app_id = app_secret = str()
    with open(args.cred) as cred_file:
        def _get_v(s):
            pattern = r"^.+?\s*=\s*[\"']?(.+?)[\"']?$"
            found = re.findall(pattern, s.strip())
            return found[0]

        for line in cred_file:
            if line.startswith("app_id"):
                app_id = _get_v(line)
            elif line.startswith("app_secret"):
                app_secret = _get_v(line)

    if not (app_id and app_secret):
        print("Error: incorrect configuration file format.")
        print()
        print("Please provide a configuration file in the correct format.")
        print("It should look something like this:")
        print()
        print("app_id = \"111111111111111\"")
        print("app_secret = \"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\"")
        print() 
        sys.exit(0)

    if args.group: # if user wants to scrape a group
        if not args.use_existing_posts_csv:
            scrape_group_posts(args.group, app_id, app_secret, args.posts_output)
        if args.scrape_comments: # if user wants to scrape comments too
            scrape_comments(args.group, app_id, app_secret, args.posts_output,
                    args.comments_output, args.scrape_author_id)

    elif args.page: # if user wants to scrape a page
        if not args.use_existing_posts_csv:
            scrape_page_posts(args.page, app_id, app_secret, args.posts_output)
        if args.scrape_comments: # if user wants to scrape comments too
            scrape_comments(args.page, app_id, app_secret, args.posts_output, 
                    args.comments_output, args.scrape_author_id)
