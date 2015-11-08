#!/usr/bin/env python3
import sys
import csv
import yaml
import os.path
import pymysql
import argparse
import prompts
from io import StringIO # For CSV export to write to a variable

class MagentoAttributeSearcher(object):
	"""Provides the ability to set up and execute searches against Attribute values."""

	def __init__(self, scope, attribute, comparison, value, outputFormat, outputLocation, automated):
		"""Initialize properties, call for config import."""

		self.scope = scope
		self.attribute = attribute
		self.comparison = comparison
		self.value = value
		self.outputFormat = outputFormat
		self.outputLocation = outputLocation
		self.automated = automated

		self.importDbConfig()

		self.validateProperties()

	def importDbConfig(self):
		"""
		If available, import database connection credentials and call for the connection to be established.
		Else, run the user through a set of prompts to retrieve that information on the command-line.
		"""

		if os.path.isfile('db.yaml'):
			with open('db.yaml') as dbConfigFile:
				dbConfig = yaml.safe_load(dbConfigFile)

			if not all(parameter in dbConfig for parameter in ['host','user','port','passwd','db']):
				print('Missing some information in "db.yaml".') # TODO make a list, iterate through it, and mark things missing to give more helpful error message (but maybe don't print the current setting that WAS found, for security reasons)

				if self.automated:
					sys.exit()

				self.promptDbCredentials()
			else:
				self.connectToDb(dbConfig['host'], dbConfig['port'], dbConfig['user'], dbConfig['passwd'], dbConfig['db'], )
		else:
			print('Could not locate "db.yaml".')

	def promptDbCredentials(self):
		"""
		Run through a few prompts to retrieve the necessary database server and authentication information.
		Offer to permanently store this information in the DB config file and do so if permitted.
		"""

		prompts.prompt('Please either end this script to set "host, port, user, passwd, db" in "db.yaml" and re-run this program, or press [Enter] to answer a few prompts to get your database credentials in order to connect you')
		host = prompts.prompt('Hostname')
		port = int(prompts.prompt('Port', '3306', ['3306']))
		user = prompts.prompt('Username')
		passwd = prompts.prompt('Password')
		db = prompts.prompt('Specific database on host to connect to')

		print('')
		print('Great! Thank you for answering those questions.')
		print('')
		print('Right now none of this information will be saved once the program closes.')

		# Offer to create the settings file that they are missing or is corrupt/wrong
		promptText = 'Would you like to save your connection details for future connections?'
		if os.path.isfile('db.yaml'):
			promptText += ' (warning: this will overwrite your current "db.yaml" file)'

		if prompts.promptYesNo(promptText):
			data = dict(
				host = host,
				port = port,
				user = user,
				passwd = passwd,
				db = db
			)
			with open('db.yaml', 'w') as outputFile:
				outputFile.write(yaml.dump(data, default_flow_style=False))
		else:
			print('Okay! None of the information entered above will be saved.')

		self.connectToDb(host, port, user, passwd, db)

	def connectToDb(self, host, port, user, passwd, db):
		"""Establish the DB connection."""

		print('Connecting to DB...')
		self.dbConn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
		self.dbCursor = self.dbConn.cursor()

	def closeDb(self):
		"""Disconnect from the DB."""

		print('Closing connection to DB...')
		self.dbConn.close()

	def listAttributes(self):
		"""List all attributes of the current scope."""

		if not self.scope:
			self.promptScope()

		self.dbCursor.execute("""SELECT * FROM (
				SELECT
					ea.attribute_id,
					ea.attribute_code,
					ea.is_required AS required
				FROM catalog_%s_entity AS ce
				LEFT JOIN eav_attribute AS ea
					ON ce.entity_type_id = ea.entity_type_id
				LEFT JOIN catalog_%s_entity_varchar AS ce_varchar
					ON ce.entity_id = ce_varchar.entity_id
					AND ea.attribute_id = ce_varchar.attribute_id
					AND ea.backend_type = 'varchar'
				LEFT JOIN catalog_%s_entity_int AS ce_int
					ON ce.entity_id = ce_int.entity_id
					AND ea.attribute_id = ce_int.attribute_id
					AND ea.backend_type = 'int'
				LEFT JOIN catalog_%s_entity_text AS ce_text
					ON ce.entity_id = ce_text.entity_id
					AND ea.attribute_id = ce_text.attribute_id
					AND ea.backend_type = 'text'
				LEFT JOIN catalog_%s_entity_decimal AS ce_decimal
					ON ce.entity_id = ce_decimal.entity_id
					AND ea.attribute_id = ce_decimal.attribute_id
					AND ea.backend_type = 'decimal'
				LEFT JOIN catalog_%s_entity_datetime AS ce_datetime
					ON ce.entity_id = ce_datetime.entity_id
					AND ea.attribute_id = ce_datetime.attribute_id
					AND ea.backend_type = 'datetime'
			) AS tab
			GROUP BY attribute_id
			ORDER BY attribute_code"""
			% (self.scope, self.scope, self.scope, self.scope, self.scope, self.scope)
		)

		return self.dbCursor

	def validateProperties(self):
		"""Initiate requests for any information necessary for the query that has not already been supplied."""

		if not self.validateScope():
			if self.automated:
				print('Invalid value "' + self.scope + '" for Scope.')
				sys.exit()

			self.promptScope()

		if not self.validateAttribute():
			if self.automated:
				print('Invalid value "' + self.scope + '" for Attribute.')
				sys.exit()

			self.promptAttribute()

		if not self.validateComparison():
			if self.automated:
				print('Invalid value "' + self.scope + '" for Comparison.')
				sys.exit()

			self.promptComparison()

		if not self.validateValue():
			if self.automated:
				print('Invalid value "' + self.scope + '" for Value.')
				sys.exit()

			self.promptValue()

		if not self.validateOutputFormat():
			if self.automated:
				print('Invalid value "' + self.scope + '" for OutputFormat.')
				sys.exit()

			self.promptOutputFormat()

		if not self.validateOutputLocation():
			if self.automated:
				print('Invalid value "' + self.scope + '" for OutputLocation.')
				sys.exit()

			self.promptOutputLocation()

	def validateScope(self):
		"""`scope` validation check."""

		if (not self.scope or
				self.scope not in ['category', 'product']):
			return False

		return True

	def promptScope(self):
		"""Prompt for what type of entity to search within."""

		self.scope = prompts.prompt('Please enter the scope of your search', 'product', ['category','product'])

		if not self.validateScope():
			print('Invalid selection.')
			self.promptScope()

	def validateAttribute(self):
		"""`attribute` validation check."""

		if not self.attribute:
			return False

		return True

	def promptAttribute(self):
		"""Prompt for which Attribute to search on (with the option to list off the possibilities if its name is unknown)."""

		# Query for Attributes
		self.attribute = prompts.prompt('Press [Enter] to retrieve a list of all available Attributes --be patient--, or provide the `attribute_code` that you are interested in now')

		if self.attribute == '':
			attributes = self.listAttributes()

			# Attributes Output
			attributesListOrFilepath = prompts.prompt('Press [Enter] to list those Attributes, or provide a filepath to save the output as a CSV', options=['`/path/to/target/file.csv`'])
			if attributesListOrFilepath == '':
				for attribute in attributes:
					print('| SKU: %s | Name: %s | Required: %s |'
						%
						(attribute[0], attribute[1], 'Yes' if attribute[2]==1 > 0 else 'No')
					)
			else:
				with open(attributesListOrFilepath, 'w', newline='') as file:
					csv_writer = csv.writer(file, delimiter=',')
					csv_writer.writerow(['SKU','Name','Required'])
					for attribute in attributes:
						csv_writer.writerow([attribute[0], attribute[1], 'Yes' if attribute[2]==1 > 0 else 'No'])

			isAttributeNeeded = True
			while isAttributeNeeded:
				self.attribute = prompts.prompt('Please provide the Attribute that you\'d like to search on')

				if self.attribute == '':
					print('I\'m sorry, but I didn\'t get anything.')
				else:
					isAttributeNeeded = False

		if not self.validateAttribute():
			print('Invalid selection.')
			self.promptAttribute()

	def validateComparison(self):
		"""`comparison` validation check."""

		if (not self.comparison or
				self.comparison not in ['=','<=>','!=','<>','<','<=','>=','>','LIKE','NOT LIKE','IS','IS NOT']):
			return False

		return True

	def promptComparison(self):
		"""Prompt for the comparison operator that they would like to use (among the list of supported ones)."""

		self.comparison = prompts.prompt('Please type the comparison operator that you would like to use', 'LIKE', ['=','<=>','!=','<>','<','<=','>=','>','LIKE','NOT LIKE','IS','IS NOT'])

		if not self.validateComparison():
			print('Invalid selection.')
			self.promptComparison()

	def validateValue(self):
		"""`value` validation check."""

		if (not self.value and
				self.value != '' and
				self.value != None):
			return False

		return True

	def promptValue(self):
		"""Prompt for Value to Compare against the chosen Attribute."""

		value = prompts.prompt('Please enter the value that you would like to search for')

		# Offer conversions for SQL reserved keywords to become special instead of the string that they currently are
		if value in ['null', 'not null']:
			print('I see that you\'re searching for a value of ' + value + '. Right now that is a literal string and has no special meaning to MySQL.')

			if prompts.promptYesNo('Would you like that converted to the reserved SQL keyword `NULL`?', 'yes'):
				if self.comparison in ['LIKE', '=']:
					self.comparison = 'IS' # Since `LIKE NULL` is not valid

					# Theoretically, the value should only ever be "NULL" in this case, but hey, if people want to put "NOT" in...
					# ...a parameter value instead the comparison operator then who am I to stop them? Alas, I will autocorrect them!
					if value == 'not null':
						self.comparison += ' NOT' # `IS NULL` -> `IS NOT NULL`

				elif self.comparison == '!=' or \
					(	self.comparison == 'IS' and \
						value == 'not null' \
					):
					self.comparison = 'IS NOT'
					# Unlike above, no need to check for a value of "NOT NULL" here since it (correctly) gets set to `None` either way

				value = None # Python `None` === MySQL `NULL`
		# If NOT a reserved keyword, then make this a `LIKE %...%` comparison
		else:
			if self.comparison == 'LIKE':
				value = '%' + value + '%'

		if not self.validateValue():
			print('Invalid selection.')
			self.promptValue()

	def validateOutputFormat(self):
		"""`outputFormat` validation check."""

		if (not self.outputFormat or
				self.outputFormat not in ['csv', 'text']):
			return False

		return True

	def promptOutputFormat(self):
		"""Prompt for how the search results should be formatted."""

		self.outputFormat = prompts.prompt('Please choose a supported output format', 'text', ['csv', 'text'])
		if not self.isOutputFormatValid():
			print('Something wasn\'t quite right...')
			self.promptOutputFormat

		if not self.validateOutputFormat():
			print('Invalid selection.')
			self.promptOutputFormat()

	def validateOutputLocation(self):
		"""`outputLocation` validation check."""

		if not self.outputLocation: # or if filepath does not exist
			return False

		return True

	def promptOutputLocation(self):
		"""Prompt for the location that the results should be output."""

		self.outputLocation = prompts.prompt('Press [Enter] to print the results to stdout, or provide a filepath to save the output as a CSV', 'stdout', ['stdout', '`/path/to/target/file.csv`'])

		if self.outputLocation == '':
			self.outputLocation = 'stdout'

		if not self.validateOutputLocation():
			print('Invalid selection.')
			self.promptOutputLocation()

	def search(self):
		"""Prompt for review and final authorization. then execute the query."""

		humanReadableAttributeValue = 'NULL' if self.value == None else "''" if self.value == '' else self.value
		searchMessage = 'Search for "' + self.attribute + ' ' + self.comparison + ' ' + humanReadableAttributeValue + '" (within the "' + self.scope + '" catalog entity)'

		if self.automated:
			print(searchMessage + '...')
		else:
			authorization = prompts.promptYesNo(searchMessage, 'yes')

			if not authorization:
				print('Okay. Cancelling search.')
				self.closeDb()
				print('Search successfully cancelled.')
				sys.exit()


		# In an ideal world, I could do string interpolation for the table names (since those can't be parameters), and
		# ...immediately follow that with the parameters for the values (since those *can* be parameters), but instead
		# ...Python just keeps saying "TypeError: not enough arguments for format string"
		# Here's an example of what I would like to do:
		# "some_%s_table INNER JOIN some_%s_other_table WHERE column1 = %s AND column1 = %s" % (tbl1, tbl2), (val1, val2)
		#
		# But instead I have to do:
		# sql1 = "some_%s_table INNER JOIN some_%s_other_table" % (tbl1, tbl2)
		# query(sql1 + "WHERE column1 =  %s AND column2 = %s", (val1, val2))
		interpolatedPortion = """SELECT
				ce.sku,
				ea.attribute_id,
				ea.attribute_code,
				CASE ea.backend_type
					WHEN 'varchar' THEN ce_varchar.value
					WHEN 'int' THEN ce_int.value
					WHEN 'text' THEN ce_text.value
					WHEN 'decimal' THEN ce_decimal.value
					WHEN 'datetime' THEN ce_datetime.value
					ELSE ea.backend_type
				END AS value,
				CASE ea.backend_type
					WHEN 'varchar' THEN ce_varchar.store_id
					WHEN 'int' THEN ce_int.store_id
					WHEN 'text' THEN ce_text.store_id
					WHEN 'decimal' THEN ce_decimal.store_id
					WHEN 'datetime' THEN ce_datetime.store_id
					ELSE ea.backend_type
				END AS store_id,
				ea.is_required AS required
			FROM catalog_%s_entity AS ce
			LEFT JOIN eav_attribute AS ea
				ON ce.entity_type_id = ea.entity_type_id
			LEFT JOIN catalog_%s_entity_varchar AS ce_varchar
				ON ce.entity_id = ce_varchar.entity_id
				AND ea.attribute_id = ce_varchar.attribute_id
				AND ea.backend_type = 'varchar'
			LEFT JOIN catalog_%s_entity_int AS ce_int
				ON ce.entity_id = ce_int.entity_id
				AND ea.attribute_id = ce_int.attribute_id
				AND ea.backend_type = 'int'
			LEFT JOIN catalog_%s_entity_text AS ce_text
				ON ce.entity_id = ce_text.entity_id
				AND ea.attribute_id = ce_text.attribute_id
				AND ea.backend_type = 'text'
			LEFT JOIN catalog_%s_entity_decimal AS ce_decimal
				ON ce.entity_id = ce_decimal.entity_id
				AND ea.attribute_id = ce_decimal.attribute_id
				AND ea.backend_type = 'decimal'
			LEFT JOIN catalog_%s_entity_datetime AS ce_datetime
				ON ce.entity_id = ce_datetime.entity_id
				AND ea.attribute_id = ce_datetime.attribute_id
				AND ea.backend_type = 'datetime'
			HAVING `value` %s """ % (self.scope, self.scope, self.scope, self.scope, self.scope, self.scope, self.comparison)

		self.dbCursor.execute("""SELECT * FROM (
				""" + interpolatedPortion + """%s
					AND `attribute_code` = %s
			) AS tab
			WHERE tab.value != ''""",
			(self.value, self.attribute)
		)

		self.getResults()

		self.closeDb()

	def getResults(self):
		"""Wrapper method for formatting and outputting results."""

		# Basically: self.output = self.formatResultsAs{{self.outputFormat}}
		if self.outputFormat == 'text':
			self.output = self.formatResultsAsText()
		elif self.outputFormat == 'csv':
			self.output = self.formatResultsAsCsv()

		if self.outputLocation == 'stdout':
			self.writeResultsToStdout()
		else:
			self.writeResultsToFile()

	def formatResultsAsText(self):
		"""Format the results as plain text/ASCII-like."""

		output = ''

		for result in self.dbCursor:
			output += '| SKU: %s | Value: %s |\n' % (result[0], result[3])

		return output

	def formatResultsAsCsv(self):
		"""Format the results as a CSV."""

		output = StringIO()
		csv_writer = csv.writer(output, delimiter=',')
		csv_writer.writerow(['SKU','Value'])

		for result in self.dbCursor:
			csv_writer.writerow([result[0], result[3]])

		return output

	def writeResultsToStdout(self):
		"""print()'s the output."""

		print(self.output)

	def writeResultsToFile(self):
		"""Places the output into a file at the location specified by the outputLocation property."""

		with open(self.outputLocation, 'w', newline='') as file:
			file.write(self.output + "\n")
			file.close()


# Start script!
parser = argparse.ArgumentParser(description='Interactive Attribute searcher for Magento.')
parser.add_argument('-a', '--attribute', help="The `attribute_code` to search on.")
parser.add_argument('-c', '--comparison', help="The comparison to use when searching for the --value.\n(default: '%(default)s')", default='LIKE')
parser.add_argument('-f', '--format', help="The format of the output.\n(default: '%(default)s')", default='text')
parser.add_argument('-o', '--output', help="Where the output should be written.\n(default: '%(default)s')", default='stdout')
parser.add_argument('-s', '--scope', help="The table to search. Example options include 'category' and 'product'.\n(default: '%(default)s')", default='product')
parser.add_argument('-v', '--value', help="The term to match against.\n(default: '%(default)s' (literal empty string))", default='')
parser.add_argument('-z', '--automated', help="Automatically conduct the search and trigger the output without user intervention.\n(default: '%(default)s')", default=False)
args = parser.parse_args()

searcher = MagentoAttributeSearcher(args.scope, args.attribute, args.comparison, args.value, args.format, args.output, args.automated)
searcher.search()
