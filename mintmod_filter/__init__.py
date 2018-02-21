"""
This package translates mintmod-flavoured LaTex to vanilla LaTeX.

It can be seen as a shim for ``mintmod.tex``. It handles important mintmod
commands translating them to regular Pandoc elements. The central function in
this module is a
:class:`Pandoc filter <mintmod_filter.filter_action.FilterAction>`.
"""
