from distutils.core import setup
from Cython.Build import cythonize

ext_modules = cythonize("homomorphism_solver.pyx")
ext_modules = cythonize(ext_modules, compiler_directives={'language_level' : "3"}, gdb_debug=True)
setup(ext_modules=ext_modules)
