import Metal

if let device = MTLCreateSystemDefaultDevice() {
    print("✅ Metal device found: \(device.name)")
    print("   Max threads per threadgroup: \(device.maxThreadsPerThreadgroup)")
    print("   Supports unified memory: \(device.hasUnifiedMemory)")
} else {
    print("❌ No Metal device found")
}