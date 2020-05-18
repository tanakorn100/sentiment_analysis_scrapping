# Facebook Page Post Scraper

This is a fork of Max Woolf's [facebook-page-post-scraper](https://github.com/minimaxir/facebook-page-post-scraper).

It only works on Python 3.

This version allows you to specify the page/group you wish to scrape and where you want CSV files to be stored through command-line arguments.

It also separates your App ID and App secret from the code; now, you have to store these credentials in a separate file.

![](/examples/fb_scraper_data.png)

A tool for gathering *all* the posts and comments of a Facebook Page (or Open Facebook Group) and related metadata, including post message, post links, and counts of each reaction on the post. All this data is exported as a CSV, able to be imported into any data analysis program like Excel.

The purpose of the script is to gather Facebook data for semantic analysis, which is greatly helped by the presence of high-quality Reaction data. Here's quick examples of a potential Facebook Reaction data visualization using data from [CNN's Facebook page](https://www.facebook.com/cnn/):

![](/examples/reaction-example-2.png)

## Usage

To scrape posts from a page:

`python3 run.py --page <page name> --cred <path to credential file> --posts-output <filepath>`

To scrape both posts and comments:

```
python3 run.py --page <page name> --cred <path to credential file> --posts-output <filepath> \
--scrape-comments --comments-output <filepath>
```

To scrape from a group, change `--page` to `--group`.

To skip downloading statuses and retrieve comments using an existing CSV file, use the `--use-existing-posts-csv` command:

```
python3 run.py --page <page name> --cred <path to credential file> --posts-output <filepath> \
--scrape-comments --comments-output <filepath> --use-existing-posts-csv
```


### Credential file format

The `-cred` command-line argument specifies where your credential file is located.

**Do not share this file with anyone.**

It should look something like this:

```
app_id = "111111111111111"
app_secret = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

You need an App ID and App Secret of a Facebook app you control (I strongly recommend creating an app just for this purpose) and the Page ID of the Facebook Page you want to scrape.

Example CSVs for CNN, NYTimes, and BuzzFeed data are not included in this repository due to size, but you can download [CNN data here](https://dl.dropboxusercontent.com/u/2017402/cnn_facebook_statuses.csv.zip) [2.7MB ZIP], [NYTimes data here](https://dl.dropboxusercontent.com/u/2017402/nytimes_facebook_statuses.csv.zip) [4.9MB ZIP], and [BuzzFeed data here](https://dl.dropboxusercontent.com/u/2017402/buzzfeed_facebook_statuses.csv.zip) [2.1MB ZIP].

### Getting the numeric group ID

For groups without a custom username, the ID will be in the address bar; for groups with custom usernames, to get the ID, do a View Source on the Group Page, search for "entity_id", and use the number to the right of that field. For example, the `group_id` of [Hackathon Hackers](https://www.facebook.com/groups/hackathonhackers/) is 759985267390294.

![](/examples/entity.png)

You can download example data for [Hackathon Hackers here](https://dl.dropboxusercontent.com/u/2017402/759985267390294_facebook_statuses.csv.zip) [4.7MB ZIP]

Keep in mind that large pages such as CNN have *millions* of comments, so be careful! (scraping throughput is approximately 87k comments/hour)

## Privacy

This scraper can only scrape public Facebook data which is available to anyone, even those who are not logged into Facebook. No personally-identifiable data is collected in the Page variant; the Group variant does collect the name of the author of the post, but that data is also public to non-logged-in users. Additionally, the script only uses officially-documented Facebook API endpoints without circumventing any rate-limits.

Note that this script, and any variant of this script, *cannot* be used to scrape data from user profiles. (and the Facebook API specifically disallows this use case!)

## Maintainer

* Koh Wei Jie

## Credits

This is a fork of Max Woolf's code at https://github.com/minimaxir/facebook-page-post-scraper

Parts of this README were copied verbatim.

## License

Be aware that this is a fork of Max Woolf's MIT-licensed code.
