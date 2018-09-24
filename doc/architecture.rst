Architecture
============

This section gives an overview of innoconv-mintmods architecture.

The command line interface
--------------------------

The entry point is the command line tool ``innoconv-mintmod``.

It calls panzer with the correct parameters.

Most of the magic happens in the package :class:`MintmodFilterAction
<innoconv_mintmod.mintmod_filter.filter_action.MintmodFilterAction>`.

It is implemented as a `Pandoc filter <https://pandoc.org/filters.html>`_
and provides functions to deal with a number of special LaTeX mintmod commands
Pandoc would otherwise just ignore.

All special commands are translated into primitives Pandoc knows already.
Additionally information is encoded in attributes that are attached to the
resulting elements.

The result of the ``MintmodFilterAction`` is a regular Pandoc AST that can
be further processed by Pandoc output modules, thus be translated to Markdown,
LaTeX, HTML and so forth.

The Pandoc JSON output is processed by
:ref:`generate_innodoc.py<generate_innodoc>`. It's implemented as a
post-flight panzer script.

panzer
------

`panzer <https://github.com/msprev/panzer>`_ is a small wrapper script around
Pandoc. It enriches Pandoc with serveral useful features that just happened to
match this projects needs.

First of all it is possible to define profiles (called *styles* in panzer)
that can already define parameters on how to run Pandoc.

Furthermore it can manage applied filters, run pre- and postprocessors etc.

You can find its configuration in the sub-directory ``.panzer``.
