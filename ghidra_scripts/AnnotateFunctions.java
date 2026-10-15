// Names functions and/or sets a plate comment, for knowledge recorded in docs/FUNCTIONS.md.
// Args: <out.txt> then items "addr#name#comment" (name may be empty = keep the name; no spaces: the headless
// .bat passes arguments through cmd, which splits on spaces and commas and treats | as a pipe). Writes the program.
// Headless: -postScript AnnotateFunctions.java <out.txt> 50001000#MyName#EXP-007:... ...
//@category SH2Perf
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

import java.io.PrintWriter;

public class AnnotateFunctions extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 1; i < args.length; i++) {
                String[] p = args[i].split("#", 3);
                Function f = getFunctionAt(toAddr(p[0]));
                if (f == null) { w.printf("%s: no function starts here, skipped%n", p[0]); continue; }
                String old = f.getName();
                if (p.length > 1 && !p[1].isEmpty()) f.setName(p[1], SourceType.USER_DEFINED);
                if (p.length > 2 && !p[2].isEmpty()) f.setComment(p[2]);
                w.printf("%s: %s -> %s, comment: %s%n", p[0], old, f.getName(), f.getComment());
            }
        }
    }
}
