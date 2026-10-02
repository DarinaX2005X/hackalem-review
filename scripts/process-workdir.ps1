# Read a Windows process's current directory without injecting code into it.
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class HackAlemProcessDirectory {
  [DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
  [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
  [DllImport("kernel32.dll")] static extern bool ReadProcessMemory(IntPtr h, IntPtr address, byte[] data, int size, out IntPtr read);
  [DllImport("ntdll.dll")] static extern int NtQueryInformationProcess(IntPtr h, int kind, IntPtr data, int size, out int returned);
  static byte[] Read(IntPtr h, long address, int size) {
    byte[] data=new byte[size]; IntPtr count;
    if(!ReadProcessMemory(h,new IntPtr(address),data,size,out count) || count.ToInt64()!=size) throw new Exception();
    return data;
  }
  static long Pointer(IntPtr h,long address,bool wow) {
    byte[] data=Read(h,address,wow?4:8);
    return wow?BitConverter.ToUInt32(data,0):BitConverter.ToInt64(data,0);
  }
  public static string Get(int pid) {
    IntPtr h=OpenProcess(0x410,false,pid); if(h==IntPtr.Zero)return null;
    IntPtr buffer=Marshal.AllocHGlobal(48);
    try {
      int returned; bool wow=false; long peb;
      if(NtQueryInformationProcess(h,26,buffer,IntPtr.Size,out returned)==0 && Marshal.ReadIntPtr(buffer)!=IntPtr.Zero) {
        wow=true; peb=Marshal.ReadIntPtr(buffer).ToInt64();
      } else {
        if(NtQueryInformationProcess(h,0,buffer,48,out returned)!=0)return null;
        peb=Marshal.ReadIntPtr(buffer,IntPtr.Size).ToInt64();
      }
      long parameters=Pointer(h,peb+(wow?0x10:0x20),wow);
      long dir=parameters+(wow?0x24:0x38);
      ushort size=BitConverter.ToUInt16(Read(h,dir,2),0);
      if(size==0 || size>32766)return null;
      return Encoding.Unicode.GetString(Read(h,Pointer(h,dir+(wow?4:8),wow),size));
    } catch { return null; }
    finally { Marshal.FreeHGlobal(buffer); CloseHandle(h); }
  }
}
'@
