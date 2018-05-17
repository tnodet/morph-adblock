#!/usr/bin/env python3

import copy, json, os, pprint, sys, urllib
import requests


def printerr(*args, **kwargs):
	"""Wrapper around print, to print to stderr"""
	print(*args, file=sys.stderr, **kwargs)


def remove_prefix_and_suffix(s, prefix, suffix):
	"""Try and remove the prefix and suffix from the given string.

	This function will try and remove the given prefix and suffix to the given string.
	If it succeeds, it returns the resulting string.
	If the string doesn't start or end with the prefix or suffix respectively, a ValueError is raised.

	Args:
		s (str): The string to be stripped of given prefix and suffix
		prefix(str): The string expected to be the beginning of s
		suffix(str): The string expected to be the ending of s

	Returns:
		str: The string without its prefix and suffix

	Raises:
		ValueError: If the string doesn't start/end with prefix/suffix
	"""
	rs = s
	if s.startswith(prefix):
		# expected begginning
		rs = rs[len(prefix):]
		if rs.endswith(suffix):
			# expected ending
			rs = rs[:-len(suffix)]
			return rs
		else:
			# unexpected begginning
			raise ValueError("Suffix doesn't match the given string:\n\tsuffix: {}\n\tstring: {}".format(suffix, s))
	else:
		# unexpected ending
		raise ValueError("Prefix doesn't match the given string:\n\tprefix: {}\n\tstring: {}".format(prefix, s))


def main(*args):

	pp = pprint.PrettyPrinter(indent=4)

	input_file_path=os.path.abspath(args[0])	# get absolute path of the file
	output_file_path=os.path.abspath(args[1])

	channel_names = list()

	# each line has the form: @@|https://www.youtube.com/*ChannelName|$document
	# we want to isolate the channel name
	prefix = '@@|https://www.youtube.com/*'
	suffix = '|$document'

	with open(input_file_path, 'r') as input_file:
		for i,line in enumerate(input_file):
			line = line.rstrip('\n')	# we remove potential trailing line-feed from the line
			try:
				channel_name = remove_prefix_and_suffix(line, prefix, suffix)	# get channel_name by removing prefix and suffix from line
			except ValueError as ve:
				# printerr(ve)
				# msg = "Line {} doesn't have the expected format:\n\tWas expecting {}<channel_name>{}\n\tGot: {}".format(i, prefix, suffix, line)
				# printerr(msg)
				pass
			else:
				channel_name = urllib.parse.unquote(channel_name)	# resulting channel_name can be URL-escaped, so we 'unquote' it
				channel_names.append(channel_name)

	# alphabetically sort the list
	channel_names = sorted(channel_names, key=lambda s: s.lower())	# case insensitive (https://stackoverflow.com/questions/10269701/case-insensitive-list-sorting-without-lowercasing-the-result)


	# YouTube API

	# declare lists
	found_channels = list()
	unfound_channels = list()
	whitelisted = list()
	blacklisted = list()

	# set common Requests parameters
	headers = {'user-agent': requests.utils.default_user_agent()+'(gzip)'}
	url = 'https://www.googleapis.com/youtube/v3/'
	with open('youtube-api-v3-credential.key', 'r') as key_file:	# get API credential from file
		key = key_file.read()


	# 1st pass: get channelId by listing channels with channel_name as Username
	# https://developers.google.com/youtube/v3/docs/channels/list
	# This request works only if the channel name we use is actually the YouTube username
	print("\n1st pass\n--------")
	resource = 'channels'

	for channel_name in channel_names:
		# part=snippet consumes 2 quota units
		payload = {'part': 'snippet', 'forUsername': channel_name, 'maxResults': 1, 'key': key}
		r = requests.get(url+resource, params=payload, headers=headers)
		r_json = r.json()
		nb_results = r_json['pageInfo']['totalResults']

		if nb_results >= 1:
			channel_id = r_json['items'][0]['id']
			channel_title = r_json['items'][0]['snippet']['title']
			found_channels.append(channel_name)
			whitelisted.append({'id': channel_id, 'username': '', 'display': channel_title})
			msg = "Channel found for Username='{}': title='{}': id='{}'".format(channel_name, channel_title, channel_id)
			print(msg)
		elif nb_results == 0:
			unfound_channels.append(channel_name)
			msg = "No channel found for Username='{}'...".format(channel_name)
			print(msg)

	# Create a temporary copy of unfoud_channel, to iterate on the original and pop items from the copy
	unfound_channels_tmp = copy.copy(unfound_channels)


	# 2nd pass: get channelId and channelTitle by searching channels with query channel_name
	# https://developers.google.com/youtube/v3/docs/channels/list
	print("\n2nd pass\n--------")
	resource = 'search'

	for channel_name in unfound_channels:
		# search consumes 100 quota units
		payload = {'q': channel_name, 'type': 'channel', 'part': 'snippet', 'maxResults': 1, 'key': key}
		r = requests.get(url+resource, params=payload, headers=headers)
		r_json = r.json()
		nb_results = r_json['pageInfo']['totalResults']

		if nb_results >= 1:
			# more than one result, we take the first result
			channel_id = r_json['items'][0]['snippet']['channelId']
			channel_title = r_json['items'][0]['snippet']['channelTitle']
			unfound_channels_tmp.remove(channel_name)
			found_channels.append(channel_name)
			whitelisted.append({'id': channel_id, 'username': '', 'display': channel_title})
			msg = "Channel found for query '{}': title='{}': id='{}'".format(channel_name, channel_title, channel_id)
			print(msg)
		elif nb_results == 0:
			# no results
			msg = "No channel found for query '{}'...".format(channel_name)
			print(msg)

	unfound_channels = unfound_channels_tmp
	#pp.pprint(found_channels)
	#pp.pprint(unfound_channels)


	# alphabetically sort the found and unfound lists
	found_channels = sorted(found_channels, key=lambda s: s.lower())
	unfound_channels = sorted(unfound_channels, key=lambda s: s.lower())

	# alphabetically sort the list of whitelisted channels
	whitelisted = sorted(whitelisted, key=lambda x: x['display'].lower())	# we sort the list on the 'display' value, case insensitive


	# Export to "YouTube Whitelister for uBlock Origin" format

	ublock_youtube_lists = {'whitelisted': whitelisted, 'blacklisted': blacklisted}
	#pp.pprint(ublock_youtube_lists)

	ublock_youtube_str = json.dumps(ublock_youtube_lists)
	#print(ublock_youtube_str)

	with open(output_file_path, 'w') as output_file:
		output_file.write(ublock_youtube_str)	# write resulting JSON str to output file


	# Write the found and unfound channels to external files (<input_file_root>.[un]found.<input_file_ext>)

	(input_file_path_root, input_file_path_ext) = os.path.splitext(input_file_path)

	found_channels_file_path = os.path.abspath(str(input_file_path_root)+".found"+str(input_file_path_ext))
	unfound_channels_file_path = os.path.abspath(str(input_file_path_root)+".unfound"+str(input_file_path_ext))

	with open(found_channels_file_path, 'w') as found_channels_file:
		for found_channel in found_channels:
			found_channels_file.write(found_channel+'\n')

	with open(unfound_channels_file_path, 'w') as unfound_channels_file:
		for unfound_channel in unfound_channels:
			unfound_channels_file.write(unfound_channel+'\n')


	return


if __name__ == '__main__':
	usage = "Usage: {} /path/to/adblock-filter-rules /path/to/ublock-filters.json".format(sys.argv[0])

	try:
		input_file = sys.argv[1]
		output_file = sys.argv[2]
	except IndexError as ie:
		#printerr(ie)
		print(usage)
		sys.exit(-1)

	sys.exit(main(input_file, output_file))