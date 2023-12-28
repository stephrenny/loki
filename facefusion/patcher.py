import subprocess
from argparse import ArgumentParser, HelpFormatter
from facefusion import metadata, wording
from facefusion.filesystem import list_directory

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])

import inquirer

PATCHES = list_directory('.patches')


def cli() -> None:
	program = ArgumentParser(formatter_class = lambda prog: HelpFormatter(prog, max_help_position = 120))
	program.add_argument('--patches', help = wording.get('apply_patch_help'), choices = PATCHES)
	program.add_argument('-v', '--version', version = metadata.get('name') + ' ' + metadata.get('version'), action = 'version')
	run(program)


def run(program : ArgumentParser) -> None:
	args = program.parse_args()

	if args.patches:
		answers =\
		{
			'patches': args.patches
		}
	else:
		answers = inquirer.prompt(
		[
			inquirer.Checkbox('patches', message = wording.get('apply_patch_help'), choices = PATCHES, ignore = not PATCHES)
		])
	if answers:
		patches = answers['patches']

		if patches:
			subprocess.run([ 'git', 'clean', 'facefusion', '-d', '-x', '-f' ])
			for patch in patches:
				subprocess.run([ 'git', 'apply', '.patches/' + patch ])
