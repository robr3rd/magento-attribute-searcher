#!/usr/bin/python3
def prompt(promptText, default='', options=[], corrections={}):
	"""
	Provide a prompt to the user.

	If `default` is supplied, capitalize that item in `options` to signify its default-ness to the user.
	If `options` is supplied, display some choices to the user. Capitalize the `default` choice if supplied.
	If `corrections` is supplied, "autocorrect" the user's response based on these values. Good for typo mitigation.

	Returns the auto-corrected, option-assisted, default-influenced string that the user entered.

	# Notes
	## Options
	If any item in the `options` parameter is passed in ALL CAPS but is not the default, then force it to lower-case.
	`.lower()` is not run on *everything* because there can be a notable UX benefit from things like CamelCase when...
	...working with complex or long option names. It is only run on ALL CAPS because otherwise the signification of...
	...one option being "more important" by means of capitalizing it is diluted, worthless, and confusing.

	## Corrections
	This should *not* be used to duplicate the functionality of `default`. There is no reason to do it, so just don't.
	"""

	# As `options` is optional, this won't run if it equals `[]` (which is Falsey)
	optionsString = '/'.join([i.upper() if i == default else i.lower() if i == i.upper() else i for i in options])
	if optionsString:
		promptText += ' (' + optionsString + ')'

	# Display the prompt!
	response = input(promptText + ': ')

	# Make use of the default functionality
	if response == '':
		response = default

	# For uniformity, lower-case the response.
	# Note: This is done *after* `default` instead of `input()` to also catch non-lower-case `default` parameter values.
	response = response.lower()

	# Corrections
	# Note that this is executed *after* `Default`...this is so that devious devs don't do dirty things like...
	# ..."autocorrecting" empty inputs when that should logically *always* be handled separately.
	for typo,correction in corrections.items():
		if response == typo.lower():
			response = correction.lower()
			break # Prevent daisy-chaining corrections, as (theoretically) a response should only need one correction.

	return response

def promptYesNo(promptText, default='no'):
	"""Wrapper for `prompt()` with convenient built-ins to process simple binary decisions."""

	options = ['yes', 'no']
	corrections = {'y':'yes', 'n':'no'}
	response = prompt(promptText, default.lower(), options, corrections)

	if response == 'yes':
		return True
	elif response == 'no':
		return False
	else: # If neither one
		return None
