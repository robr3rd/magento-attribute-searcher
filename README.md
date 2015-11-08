# Magento Attribute Searcher
As I could not find anything out-of-the-box that could show me a list of Products or Categories that had certain Attribute values, I created this little (optionally) interactive Python script.

## Requirements
- Python 3
- virtualenv

## Installation
Just fire up a new virtualenv (Python 3) and make sure that `pymysql` and `pyyaml` are installed.

### Details
1. Create a new Python 3 virtual environment.
	- Code: `virtualenv -p python3 env`
2. Activate the environment.
	- Code: `source [your environment name]/bin/activate`
3. Install the necessary modules.
	- Code: `pip install pyyaml pymysql`

## Usage
For the fully interactive version, just run without arguments: `Magento-Attribute-Searcher.py`

The script can also be run *with* arguments: `Magento-Attribute-Searcher.py -a=color --value=red --automated=True`.

### Arguments
Up-to-date documentation is always available by running the script with the `-h` or `--help` flag. Its current output as of this writing is:

```
usage: Magento-Attribute-Searcher.py [-h] [-a ATTRIBUTE] [-c COMPARISON]
                                     [-f FORMAT] [-o OUTPUT] [-s SCOPE]
                                     [-v VALUE] [-z AUTOMATED]

Interactive Attribute searcher for Magento.

optional arguments:
  -h, --help            show this help message and exit
  -a ATTRIBUTE, --attribute ATTRIBUTE
                        The `attribute_code` to search on.
  -c COMPARISON, --comparison COMPARISON
                        The comparison to use when searching for the --value.
                        (default: 'LIKE')
  -f FORMAT, --format FORMAT
                        The format of the output. (default: 'text')
  -o OUTPUT, --output OUTPUT
                        Where the output should be written. (default:
                        'stdout')
  -s SCOPE, --scope SCOPE
                        The table to search. Example options include
                        'category' and 'product'. (default: 'product')
  -v VALUE, --value VALUE
                        The term to match against. (default: '' (literal empty
                        string))
  -z AUTOMATED, --automated AUTOMATED
                        Automatically conduct the search and trigger the
                        output without user interaction. (default: 'False')
```

### Configuration
Database credentials can be pre-configured in a `db.yaml` file located at the same level as the script's primary file. If proper credentials are not found, then the script will offer to create this file for you from your interactive answers so that you won't have to re-enter them in the future. An example of that file's contents:

```yaml
db: dbname
host: host
passwd: P4$$w0rD
port: 3306
user: root
```

This file is already configured in `.gitignore`, so you need not worry about accidentally leaking credentials.
