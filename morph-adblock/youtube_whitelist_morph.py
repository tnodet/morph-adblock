#!/usr/bin/env python3

import os,sys
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

	file_path=os.path.abspath(args[0])	# get absolute path of the file

	file = open(file_path, 'r')

	channel_names = list()

	for i,line in enumerate(file):
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

	file.close()

	# alphabetically sort the list
	#channel_names.sort()	# case sensitive: Uppercase comes before lowercase
	channel_names = sorted(channel_names, key=lambda s: s.lower())	# case insensitive (https://stackoverflow.com/questions/10269701/case-insensitive-list-sorting-without-lowercasing-the-result)


	# YouTube API


	headers = {'user-agent': requests.utils.default_user_agent()+'(gzip)'}
	url = 'https://www.googleapis.com/youtube/v3/'
	resource = 'channels'

	with open('youtube-api-v3-credential.key', 'r') as key_file:
		key = key_file.read()

	for channel_name in channel_names:
		payload = {'part': 'id', 'forUsername': channel_name, 'key': key}

		r = requests.get(url+resource, params=payload, headers=headers)

		#print(r.url)
		#print(r.request.headers)
		#print(r.headers)
		#print(r.text)

		r_json = r.json()
		nb_results = r_json['pageInfo']['totalResults']

		if nb_results >= 1:
			channel_id = r_json['items'][0]['id']
			if nb_results == 1:
				msg = "Channel found forUsername='{}': id={}".format(channel_name,channel_id)
				print(msg)
			else:
				msg = "Several channels found forUsername='{}'! Selected first id={}".format(channel_name,channel_id)
				print(msg)
		elif nb_results == 0:
			msg = "No channel found forUsername='{}'...".format(channel_name)
			print(msg)


	return


if __name__ == '__main__':
	usage = "Usage: {} /path/to/adblock-filter-rules".format(sys.argv[0])

	try:
		input_file = sys.argv[1]
	except IndexError as ie:
		#printerr(ie)
		print(usage)
		sys.exit(-1)

	sys.exit(main(input_file))