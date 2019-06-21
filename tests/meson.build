project('MesonAPIdemo',  default_options : ['default_library=static'])


if add_languages('c', required: false)
  c_exe = executable('minimal_c', 'src/minimal.c')
  test('Minimal_C', c_exe)
endif

if add_languages('cpp', required: false)
  cxx_exe = executable('minimal_cxx', 'src/minimal.cxx')
  test('Minimal_CXX', cxx_exe)
endif

if add_languages('fortran', required: false)
  fortran_exe = executable('minimal_fortran', 'src/minimal.f90')
  test('Minimal_Fortran', fortran_exe)
endif

if false
if add_languages('objc', required: false)
  objc_exe = executable('minimal_objc', 'src/minimal.m')
  test('Minimal_ObjC', objc_exe)
endif

if add_languages('objcpp', required: false)
  objcpp_exe = executable('minimal_objcpp', 'src/minimal.mm')
  test('Minimal_ObjC++', objcpp_exe)
endif
endif