// Read-only export of bounded existing instruction ranges, including non-function labels.
// Args: output-dir f:entryVA | r:startVA:endVA | d:startVA:length ...
// No analysis, disassembly, or database changes.
//@category SH2Perf
import java.io.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
public class PoseSampleExtent extends GhidraScript {
 public void run() throws Exception {
  String sha=currentProgram.getExecutableSHA256();
  if (!sha.equals("94d56fd7e9ef8adde51425da339722a584e28e71235bc8a89d8175c2276050fd") && !sha.equals("f3ccdf9bb41158202dffc000e5f2036a82f4c1ce8c5c89462f6140000f32d34b")) throw new IllegalArgumentException("Unknown program identity");
  String[] a=getScriptArgs();
  if(a.length<2 || a.length>65) throw new IllegalArgumentException("Argument budget");
  File dir=new File(a[0]);
  if(!dir.isDirectory() && !dir.mkdirs()) throw new IOException("Cannot create output directory");
  long total=0;
  try(PrintWriter meta=new PrintWriter(new File(dir,"identity.txt"),"UTF-8")) {
   meta.println("sha256\t"+sha); meta.println("imagebase\t"+currentProgram.getImageBase());
   for(int j=1;j<a.length;j++) {
    String[] r=a[j].split(":",-1);
    if(r.length<2 || !(r[0].equals("f") && r.length==2 || (r[0].equals("r") || r[0].equals("d")) && r.length==3)) throw new IllegalArgumentException("Invalid mode/tokens");
    if(!r[1].matches("[0-9a-fA-F]{8}") || r[0].equals("r") && !r[2].matches("[0-9a-fA-F]{8}")) throw new IllegalArgumentException("Invalid address token");
    if(r[0].equals("d") && !r[2].matches("[1-9][0-9]{0,4}")) throw new IllegalArgumentException("Invalid data length");
    Address lo=toAddr(r[1]), hi;
    AddressSetView body;
    if(r[0].equals("f")) {
     Function f=getFunctionAt(lo); if(f==null) throw new IllegalArgumentException("Missing function");
     body=f.getBody(); hi=body.getMaxAddress();
     meta.println("function\t"+f.getEntryPoint()+"\t"+f.getName()+"\t"+body.getNumAddresses());
    } else {
     hi=r[0].equals("d") ? lo.add(Integer.parseInt(r[2])-1) : toAddr(r[2]);
     body=new AddressSet(lo,hi);
    }
    if(hi.subtract(lo)<0 || hi.subtract(lo)>65535) throw new IllegalArgumentException("Range budget");
    total+=body.getNumAddresses(); if(total>131072) throw new IllegalArgumentException("Total byte budget");
    meta.println("range\t"+a[j]);
    try(PrintWriter out=new PrintWriter(new File(dir,a[j].replace(':','-')+".txt"),"UTF-8")) {
     if(r[0].equals("d")) {
      byte[] data=new byte[(int)hi.subtract(lo)+1];
      if(currentProgram.getMemory().getBytes(lo,data)!=data.length) throw new IOException("Incomplete data read");
      StringBuilder b=new StringBuilder(); for(byte v:data)b.append(String.format("%02x",v&255));
      out.println(lo+"\t"+b+"\tdata");
     } else for(Instruction i:currentProgram.getListing().getInstructions(body,true)) {
      StringBuilder b=new StringBuilder(); for(byte v:i.getBytes()) b.append(String.format("%02x",v&255));
      out.println(i.getAddress()+"\t"+b+"\t"+i);
     }
     if(out.checkError())throw new IOException("Output write failed");
    }
   }
   if(meta.checkError())throw new IOException("Metadata write failed");
  }
 }
}
