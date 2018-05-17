# Morph-AdBlock

Morph-AdBlock aspires to be a set of scripts to **convert [AdBlock](https://www.getadblock.com/) filter rules** to their [**uBlock Origin**](https://github.com/gorhill/uBlock) counterparts.
For now, it has one script, that converts *AdBlock*'s whitelisted YouTube channels to a *YouTube Channel Whitelist for uBlock Origin* list.

## Requirements

* Python3: https://www.python.org/downloads/
* A Google Developers Console API key: https://developers.google.com/youtube/v3/getting-started
* Third-party Python libraries:

   [`requests`](http://docs.python-requests.org/en/master/)  
   [`unidecode`](https://pypi.org/project/Unidecode/)

## Functionnalities

### Convert YouTube channel whitelist (AdBlock -> uBlock)

The `youtube_whitelist_morph.py` script converts whitelisted YouTube channels rules from [*AdBlock*](https://www.getadblock.com/) to [*YouTube Channel Whitelist for uBlock Origin*](https://github.com/x0a/YouTube-Channel-Whitelist-for-uBlock-Origin).

#### Usage

```
python3 morph-adblock/youtube_whitelist_morph.py <adblock-filters.txt> <ublock-filters.json>
```

* `<adblock-filters.txt>`: file containing the whitelisted channels in *AdBlock*'s syntax (see Rules syntax). Lines that are not YouTube whitelisted channels rules will simply be ignored.
* `<ublock-filters.json>`: file to which the resulting lists will be written, in JSON format (see Rules syntax). Warning: the file will be **overwritten without notice** if it already exists!

You'll need to put your YouTube API key in the file `morph-adblock/youtube-api-v3-credential.key`.

The script will produce the following output:
* on `stdout` (terminal), lines ressembling:
  ```
  Channel found for search query 'PewDiePie': title='PewDiePie': id='UC-lHJZR3Gqxm24_Vd_AJ5Yw'
  No channel found for search query 'TaylorSwift'...
  ```
* main output file (`<ublock-filters.json>`)
* two additionnal files, `<adblock-filters>.found<.txt>` and `<adblock-filters>.unfound<.txt>`, listing found and unfound channels

#### Rules syntax

- *AdBlock* rules (found in `Options -> Customize`) have this syntax:
  ```
  @@|https://www.youtube.com/*PewDiePie|$document
  @@|https://www.youtube.com/*TaylorSwift|$document
  ```
  Note: don't worry about URL-escaped characters (e.g. `%26` instead of `&`), the script converts them.

- *YouTube Channel Whitelist for uBlock Origin* rules (found in `Settings -> Export lists`) have this syntax (JSON):

  ```json
  {
    "whitelisted": [{
      "id": "UC-lHJZR3Gqxm24_Vd_AJ5Yw",
      "username": "",
      "display": "PewDiePie"
    }, {
      "id": "UCqECaJ8Gagnn7YCbPEzWH6g",
      "username": "",
      "display": "Taylor Swift"
    }],
    "blacklisted": []
  }
  ```

#### Functionning details

The script uses the YouTube API to try and find channels matching the channel names extracted from input file.

For now, the script does 3 passes:
1. Find a channel by its YouTube `Username`. It consumes only 2 quota units. It can result in a false-positive in case the query matches a username who is not the owner of the expected channel (in other words, if a user has the same username as another channel title).
2. Search a channel, the query being the input channel name. It consumes 100 quota units. Bear in mind that the script always pick the first result, and that results are sorted by relevance.
3. Same method as the previous pass, but input channel names are converted to all-ASCII letters only (e.g. `Contes-d'1été` becomes `Contes d ete`)

## TODO

`youtube_whitelist_morph.py`:
* New pass: use a syntax- and dictionnary-based system to add spaces in the input channel names, thus improving search results
* Make the first pass (find by username) optionnal

Other:
* script to convert general AdBlock whitelist rules to uBlock origin whitelist rules
