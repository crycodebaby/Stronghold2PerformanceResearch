// Exports every function of the current program: entry, body range(s), name and name source.
// Headless: -postScript ExportFunctions.java <out.csv>
// Columns: entry,min,max,body_bytes,ranges,name,source,thunk   (addresses hex, image-base absolute)
// Addresses, names and counts only (D008); no decompiled code.
//@category SH2Perf
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.AddressRange;
import ghidra.program.model.address.AddressSetView;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

import java.io.PrintWriter;

public class ExportFunctions extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) { printerr("usage: ExportFunctions.java <out.csv>"); return; }
        int n = 0;
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            w.println("entry,min,max,body_bytes,ranges,name,source,thunk");
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext() && !monitor.isCancelled()) {
                Function f = it.next();
                AddressSetView body = f.getBody();
                StringBuilder ranges = new StringBuilder();
                for (AddressRange r : body.getAddressRanges()) {
                    if (ranges.length() > 0) ranges.append(';');
                    ranges.append(String.format("%08X-%08X", r.getMinAddress().getOffset(), r.getMaxAddress().getOffset()));
                }
                w.printf("%08X,%08X,%08X,%d,%s,%s,%s,%d%n",
                    f.getEntryPoint().getOffset(), body.getMinAddress().getOffset(), body.getMaxAddress().getOffset(),
                    body.getNumAddresses(), ranges, f.getName().replace(',', '_'), f.getSymbol().getSource(), f.isThunk() ? 1 : 0);
                n++;
            }
        }
        println("ExportFunctions: " + n + " functions -> " + args[0] + " (image base " + currentProgram.getImageBase() + ")");
    }
}
