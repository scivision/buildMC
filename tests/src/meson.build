project('MesonAPIdemo', 'c')

cc = meson.get_compiler('c')
minimal_c = executable('minimal_c', 'minimal.c')
test('MinimalC', minimal_c)

if add_languages('cpp', required: false)
  minimal_cxx = executable('minimal_cxx', 'minimal.cxx')
  test('MinimalCXX', minimal_cxx)
endif

if add_languages('fortran', required: false)
  minimal_fortran = executable('minimal_fortran', 'minimal.f90')
  test('MinimalFortran', minimal_fortran)
endif