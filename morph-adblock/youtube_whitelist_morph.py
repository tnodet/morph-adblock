#!/usr/bin/env python3

import json, os, pprint, sys
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
	input_file = open(input_file_path, 'r')

	output_file_path=os.path.abspath(args[1])

	channel_names = list()

	for i,line in enumerate(input_file):
		# each line has the form: @@|https://www.youtube.com/*ChannelName|$document
		# we want to isolate the channel name
		prefix = '@@|https://www.youtube.com/*'
		suffix = '|$document'
		line = line.rstrip('\n\r')	# we remove trailing CR/LF from the line

		try:
			channel_name = remove_prefix_and_suffix(line, prefix, suffix)
			channel_names.append(channel_name)
		except ValueError as ve:
			# printerr(ve)
			# msg = "Line {} doesn't have the expected format:\n\tWas expecting {}<channel_name>{}\n\tGot: {}".format(i, prefix, suffix, line)
			# printerr(msg)
			pass

	input_file.close()

	# alphabetically sort the list
	#channel_names.sort()	# case sensitive: Uppercase comes before lowercase
	channel_names = sorted(channel_names, key=lambda s: s.lower())	# case insensitive (https://stackoverflow.com/questions/10269701/case-insensitive-list-sorting-without-lowercasing-the-result)


	# YouTube API

	# This request works only if the channel name we use is actually the YouTube username
	headers = {'user-agent': requests.utils.default_user_agent()+'(gzip)'}
	url = 'https://www.googleapis.com/youtube/v3/'
	resource = 'channels'

	with open('youtube-api-v3-credential.key', 'r') as key_file:
		key = key_file.read()

	found_channels = list()
	unfound_channels = list()
	whitelisted = list()
	blacklisted = list()

	for channel_name in channel_names:
		payload = {'part': 'id', 'forUsername': channel_name, 'key': key}

		r = requests.get(url+resource, params=payload, headers=headers)

		r_json = r.json()
		nb_results = r_json['pageInfo']['totalResults']

		if nb_results >= 1:
			channel_id = r_json['items'][0]['id']
			found_channels.append(channel_name)
			whitelisted.append({'id': channel_id, 'username': '', 'display': channel_name})
			if nb_results == 1:
				msg = "Channel found forUsername='{}': id={}".format(channel_name,channel_id)
				#print(msg)
			else:
				msg = "Several channels found forUsername='{}'! Selected first id={}".format(channel_name,channel_id)
				#print(msg)
		elif nb_results == 0:
			unfound_channels.append(channel_name)
			msg = "No channel found forUsername='{}'...".format(channel_name)
			#print(msg)


	# Export to "YouTube Whitelister for uBlock Origin" format

	ublock_youtube_lists = {'whitelisted': whitelisted, 'blacklisted': blacklisted}
	#pp.pprint(ublock_youtube_lists)

	ublock_youtube_str = json.dumps(ublock_youtube_lists)
	#print(ublock_youtube_str)

	#print(output_file_path)

	with open(output_file_path, 'w') as output_file:
		print(output_file)
		output_file.write(ublock_youtube_str)	# write resulting JSON str to output file

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