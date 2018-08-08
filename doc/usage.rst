.. _usage:

How to use ``innoconv-mintmod``
===============================

You can run the converter in your content directory.

.. code-block:: console

  $ innoconv-mintmod .

This will trigger the conversion for this folder.

Command line arguments
----------------------

.. argparse::
   :module: innoconv_mintmod.__main__
   :func: get_arg_parser
   :prog: innoconv_mintmod
   :nodescription:
   :noepilog:
