from distutils.core import setup
import py2exe


setup(console=['game.py'], 
	options = {
			'py2exe': {
				'packages': ['summonerwars']
			}
	}
)