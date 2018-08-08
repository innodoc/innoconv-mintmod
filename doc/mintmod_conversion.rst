Converting legacy mintmod content
=================================

In this chapter some findings are documented on how to prepare content so it
can be read by the :ref:`innoconv-mintmod command <usage>`.

.. note::

  It's not a complete list and there might be things missing that need to be
  done in your specific case.

First of all make sure all content is `UTF-8 encoded`. If not, tools like
`iconv <https://www.gnu.org/savannah-checkouts/gnu/libiconv/documentation/libiconv-1.15/iconv.1.html>`_
can be helpful.

Adjust commands
---------------

There are some mintmod commands Pandoc is not able to parse. You need to
manually replace them throughout your project.

Remove ``\ifttm…\else…\fi`` commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``mintmod_ifttm`` can get rid of all ``\ifttm`` commands.

Usage:

.. code:: shell

    $ mintmod_ifttm < file_in.tex > file_out.tex

Automate on many files:

.. code:: shell

    $ find . -name '*.tex' | xargs -I % sh -c 'mintmod_ifttm < % > %_changed && mv %_changed %'

.. warning::

  The script cares only about ``\ifttm…\else…\fi`` with an ``\else`` command.
  There may be occurences of ``\ifttm…\fi`` (without ``\else``). You need to
  remove them manually!

Unwanted LaTeX commands
~~~~~~~~~~~~~~~~~~~~~~~

A couple of commands are superflous or doesn't make sense in a web-first
content publishing platform like innoDoc. So remove any occurences of the
following commands.

- ``\input{mintmod.tex}``
- ``\input{english.tex}``
- ``\begin{document}`` ``\begin{document}``
- ``\MPragma{MathSkip}``
- ``\Mtikzexternalize``
- ``\relax``
- ``\-`` (hyphenation)
- ``\pagebreak``
- ``\newpage``
- ``\MPrintIndex``
- ``\relax``

Automate:

.. code:: shell

  find . -type f -name '*.tex' -or -name '*.rtex' | xargs perl -i -pe 's/\\input{mintmod(.tex|)}\w*\n//igs'

Including other modules
~~~~~~~~~~~~~~~~~~~~~~~

Pandoc doesn't understand ``\IncludeModule``. Change these statements to proper
LaTeX commands.

``\IncludeModule{folder}{file.tex}`` → ``\input{folder/file.tex}``.

Replace strings
---------------

There are a couple of special characters you need to replace yourself.

-  ``\"a`` → ``ä``
-  ``\"o`` → ``ö``
-  ``\"u`` → ``ü``
-  ``\"A`` → ``Ä``
-  ``\"O`` → ``Ö``
-  ``\"U`` → ``Ü``

.. raw:: html

   <!-- -->

-  ``\"s`` → ``ß``
-  ``\"s`` → ``ß``
-  ``{\ss}`` → ``ß``
-  ``\ss `` → ``ß``
-  ``\ss\`` → ``ß``
-  ``\ss{}`` → ``ß``
-  ``\ss`` → ``ß``

.. raw:: html

   <!-- -->

-  ``"a`` → ``ä``
-  ``"o`` → ``ö``
-  ``"u`` → ``ü``
-  ``"A`` → ``Ä``
-  ``"O`` → ``Ö``
-  ``"U`` → ``Ü``

.. raw:: html

   <!-- -->

-  ``"``` → ``„``
-  `````` → ``„``
-  ``''`` → ``“``
-  ``"'`` → ``“``

Automate:

.. code:: shell

    find . -type f -name '*.tex' -or -name '*.rtex' | xargs sed -i 's/\\"a/ä/g'

Clean up code
-------------

Remove unused files from your project and keep track of your changes using
a VCS.
