// Compact structural summary of one function: size, blocks, loops, callers,
// callees, referenced strings. No decompiled code (DECISIONS D008).
//
// Args: <address hex> <output file>
// Output: <= 30 lines of plain text.
// @category SH2Perf
import java.io.File;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeSet;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.block.BasicBlockModel;
import ghidra.program.model.block.CodeBlock;
import ghidra.program.model.block.CodeBlockIterator;
import ghidra.program.model.block.CodeBlockReference;
import ghidra.program.model.block.CodeBlockReferenceIterator;
import ghidra.program.model.data.StringDataInstance;
import ghidra.program.model.listing.Data;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.symbol.Reference;

public class FunctionBrief extends GhidraScript {

    @Override
    protected void run() throws Exception {
        String[] args = getScriptArgs();
        Address addr = toAddr(args[0]);
        File outFile = new File(args[1]);
        Function f = getFunctionContaining(addr);

        try (PrintWriter out = new PrintWriter(outFile, "UTF-8")) {
            if (f == null) {
                out.println("no function contains " + addr);
                return;
            }
            Address entry = f.getEntryPoint();
            out.printf("function %s @ %s (+0x%x)  size %d B  params %d%n", f.getName(true), entry,
                addr.subtract(entry), f.getBody().getNumAddresses(), f.getParameterCount());

            // Blocks and back edges (a back edge to an earlier block ~ a loop).
            BasicBlockModel model = new BasicBlockModel(currentProgram);
            int blocks = 0;
            int backEdges = 0;
            CodeBlockIterator bit = model.getCodeBlocksContaining(f.getBody(), monitor);
            while (bit.hasNext()) {
                CodeBlock b = bit.next();
                blocks++;
                CodeBlockReferenceIterator dests = b.getDestinations(monitor);
                while (dests.hasNext()) {
                    CodeBlockReference r = dests.next();
                    if (f.getBody().contains(r.getDestinationAddress())
                        && r.getDestinationAddress().compareTo(b.getFirstStartAddress()) <= 0) {
                        backEdges++;
                    }
                }
            }
            out.printf("basic blocks %d  back edges (loops) %d%n", blocks, backEdges);

            // Callers.
            List<String> callers = new ArrayList<>();
            for (Function c : f.getCallingFunctions(monitor)) {
                callers.add(c.getName(true) + "@" + c.getEntryPoint());
            }
            out.printf("callers %d: %s%n", callers.size(),
                String.join(", ", callers.subList(0, Math.min(5, callers.size()))));

            // Callees with call-site counts; indirect calls counted separately.
            Map<String, Integer> callees = new HashMap<>();
            int indirect = 0;
            TreeSet<String> strings = new TreeSet<>();
            for (Instruction ins : currentProgram.getListing().getInstructions(f.getBody(), true)) {
                if (ins.getFlowType().isCall()) {
                    Address[] flows = ins.getFlows();
                    if (flows.length == 0) {
                        indirect++;
                    }
                    for (Address t : flows) {
                        Function callee = getFunctionAt(t);
                        String n = callee != null ? callee.getName(true) + "@" + t : t.toString();
                        callees.merge(n, 1, Integer::sum);
                    }
                }
                for (Reference ref : ins.getReferencesFrom()) {
                    Data d = getDataAt(ref.getToAddress());
                    if (d != null && d.hasStringValue() && strings.size() < 6) {
                        String s = StringDataInstance.getStringDataInstance(d).getStringValue();
                        if (s != null) {
                            strings.add(s.length() > 60 ? s.substring(0, 60) + "..." : s);
                        }
                    }
                }
            }
            out.printf("direct callees %d (distinct), indirect calls (vtable/pointer) %d%n", callees.size(), indirect);
            callees.entrySet().stream()
                .sorted((a, b) -> b.getValue() - a.getValue())
                .limit(15)
                .forEach(e -> out.printf("  %3dx %s%n", e.getValue(), e.getKey()));
            out.printf("strings %d:%n", strings.size());
            for (String s : strings) {
                out.println("  \"" + s.replace("\n", "\\n") + "\"");
            }
        }
    }
}
