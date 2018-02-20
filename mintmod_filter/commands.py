r"""Handle mintmod LaTex commands.

Convention: Provide a ``handle_CMDNAME`` function for handling ``CMDNAME``
command. You need to slugify the command name.

Example: ``handle_msection`` method will receive the ``\MSection`` command.
"""

import panflute as pf
from mintmod_filter.utils import handle_header, debug


class Commands():
    def handle_msection(self, args, elem, doc):
        """Remember ``MSection`` name for later.

        `MSectionStart` environment will use this information later.
        """
        handle_header(title=args[0], level=2, doc=doc, auto_id=True)
        return []

    def handle_msubsection(self, args, elem, doc):
        """Handle `MSubsection`"""
        return handle_header(title=args[0], level=3, doc=doc, auto_id=True)

    def handle_mtitle(self, args, elem, doc):
        """Handle `MTitle`` command.

        These is an equivalent to ``subsubsection``
        """
        return handle_header(title=args[0], level=4, doc=doc, auto_id=True)

    def handle_mlabel(self, args, elem, doc):
        """Handle `MLabel` command.

        Will search for the previous header element and update its id to the
        id defined in the `MLabel` command."""
        last_header_elem = getattr(doc, "last_header_elem", None)

        if last_header_elem is None:
            debug("WARNING: last_header_elem undefined in handle_mlabel with"
                  "args:" % args)
            return

        last_header_elem.identifier = args[0]

    def handle_special(self, args, elem, doc):
        """Handle `special` command.

        This command is used to embed HTML in LaTeX source.
        """
        # TODO: is this ok to do? should check for format==html?
        #       other output formats may not be able to handle this
        if "html:" in args[0]:
            html_code = args[0].replace("html:", "")
            return pf.RawBlock(html_code)
        else:
            return None

    def handle_msubject(self, args, elem, doc):
        """Handle `MSubject{title}` command.

        Command defines the document title.
        """
        meta = doc.metadata
        meta['title'] = pf.MetaString(args[0])
        doc.metadata = meta
        return []

    def handle_mdeclaresiteuxid(self, args, elem, doc):
        """Handle `MDeclareSiteUXID` command.

        This command is used to embed IDs. This is not relevant anymore and
        becomes a no-op.
        """
        return self._noop()

    def handle_mmodstartbox(self, args, elem, doc):
        """Handle `MModStartBox` command.

        This command displays a table of content for the current chapter. This
        is handled elswhere and becomes a no-op.
        """
        return self._noop()

    def _noop(self):
        """Return no elements."""
        return []