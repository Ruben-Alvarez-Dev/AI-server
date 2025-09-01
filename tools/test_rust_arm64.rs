fn main() {
    println!("✅ Rust ARM64 compilation test");
    println!("   Architecture: {}", std::env::consts::ARCH);
    println!("   OS: {}", std::env::consts::OS);
    println!("   Family: {}", std::env::consts::FAMILY);
    
    // Test some basic operations
    let numbers: Vec<i32> = (1..=10).collect();
    let sum: i32 = numbers.iter().sum();
    println!("   Sum of 1-10: {}", sum);
    
    // Test system information
    println!("   Available parallelism: {:?}", std::thread::available_parallelism());
    
    println!("✅ ARM64 compilation successful!");
}