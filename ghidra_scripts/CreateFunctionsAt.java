// Creates a function at each given address where code starts and no function exists yet (Ghidra's own
// body computation). For entries that the auto-analysis missed because they are only reached through
// data pointers. Prints entry and body per address. Writes the program (no -readOnly).
// Headless: -postScript CreateFunctionsAt.java <out.txt> <addr hex> [...]
//@category SH2Perf
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;

import java.io.PrintWriter;

public class CreateFunctionsAt extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        try (PrintWriter w = new PrintWriter(args[0], "UTF-8")) {
            for (int i = 1; i < args.length; i++) {
                Address a = toAddr(args[i]);
                Function f = getFunctionContaining(a);
                if (f != null) { w.printf("%s: already in %s@%s, unchanged%n", a, f.getName(), f.getEntryPoint()); continue; }
                if (getInstructionAt(a) == null) { w.printf("%s: no instruction starts here, skipped%n", a); continue; }
                f = createFunction(a, null);
                if (f == null) { w.printf("%s: createFunction failed%n", a); continue; }
                w.printf("%s: created %s body %s-%s (%d bytes)%n", a, f.getName(), f.getBody().getMinAddress(),
                    f.getBody().getMaxAddress(), f.getBody().getNumAddresses());
            }
        }
    }
}
