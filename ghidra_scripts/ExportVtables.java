// Export RTTI-derived virtual function tables as CSV (addresses + names only,
// no decompiled code). Run after auto-analysis with the MSVC RTTI analyzer.
//
// Output: <arg0 or ~/sh2_vtables.csv> with columns
//   class,vtable,slot,function,function_name,size_bytes,callers
// @category SH2Perf
import java.io.File;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;

public class ExportVtables extends GhidraScript {

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        File out = new File(args.length > 0 ? args[0]
            : System.getProperty("user.home") + File.separator + "sh2_vtables.csv");
        Memory mem = currentProgram.getMemory();
        int ptrSize = currentProgram.getDefaultPointerSize();
        int tables = 0;
        int rows = 0;

        try (PrintWriter pw = new PrintWriter(out, "UTF-8")) {
            pw.println("class,vtable,slot,function,function_name,size_bytes,callers");
            SymbolIterator it = currentProgram.getSymbolTable().getSymbols("vftable");
            while (it.hasNext() && !monitor.isCancelled()) {
                Symbol vt = it.next();
                String cls = vt.getParentNamespace().getName(true);
                Address a = vt.getAddress();
                tables++;
                for (int slot = 0; slot < 512; slot++) {
                    Address entry = a.add((long) slot * ptrSize);
                    if (slot > 0 && currentProgram.getSymbolTable().getPrimarySymbol(entry) != null
                        && currentProgram.getSymbolTable().getPrimarySymbol(entry).getName().contains("vftable")) {
                        break; // next table starts
                    }
                    long target;
                    try {
                        target = Integer.toUnsignedLong(mem.getInt(entry));
                    } catch (Exception e) {
                        break;
                    }
                    Address fa = a.getNewAddress(target);
                    Function f = getFunctionAt(fa);
                    if (f == null) {
                        break;
                    }
                    int callers = getReferencesTo(fa).length;
                    pw.printf("\"%s\",%s,%d,%s,\"%s\",%d,%d%n", cls, a, slot, fa, f.getName(true),
                        f.getBody().getNumAddresses(), callers);
                    rows++;
                }
            }
        }
        println("ExportVtables: " + tables + " vtables, " + rows + " slots -> " + out);
    }
}
