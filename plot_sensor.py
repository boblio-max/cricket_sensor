import json
import time
import matplotlib.pyplot as plt
import os

def plot_sensor_data(log_file, device_id="unknown"):
    times = []
    accel_mags = []
    gyro_mags = []
    
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    with open(log_file, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                times.append(data.get('t', len(times)))
                accel_mags.append(data.get('a_mag', 0))
                gyro_mags.append(data.get('g_mag', 0))
            except json.JSONDecodeError:
                continue
    
    plt.ion()
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(f'Sensor Data - {device_id}', fontsize=16)
    
    line1, = ax1.plot([], [], 'r-', label='Accel Magnitude', linewidth=2)
    line2, = ax2.plot([], [], 'b-', label='Gyro Magnitude', linewidth=2)
    
    ax1.set_title('Accelerometer Magnitude (g)', fontsize=12)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Magnitude (g)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2.set_title('Gyroscope Magnitude (deg/s)', fontsize=12)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Magnitude (deg/s)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    max_points = 1000
    x_data = []
    y1_data = []
    y2_data = []
    
    def update_plot(i):
        nonlocal x_data, y1_data, y2_data
        
        start_idx = max(0, i - max_points + 1)
        x_data = times[start_idx:i+1] if i < len(times) else times[-max_points:]
        y1_data = accel_mags[start_idx:i+1] if i < len(accel_mags) else accel_mags[-max_points:]
        y2_data = gyro_mags[start_idx:i+1] if i < len(gyro_mags) else gyro_mags[-max_points:]
        
        line1.set_data(x_data, y1_data)
        line2.set_data(x_data, y2_data)
        
        ax1.relim()
        ax1.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()
        
        ax1.set_xlim(min(x_data) if x_data else 0, max(x_data) if x_data else 10)
        ax2.set_xlim(min(x_data) if x_data else 0, max(x_data) if x_data else 10)
        
        fig.canvas.draw()
        fig.canvas.flush_events()
    
    print("Starting real-time plot. Press Ctrl+C to stop.")
    
    try:
        for i in range(len(times)):
            update_plot(i)
            time.sleep(0.01)
        
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nPlot stopped by user")
    finally:
        plt.ioff()
        plt.close()

if __name__ == "__main__":
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description='Plot sensor data from JSONL log file')
    parser.add_argument('log_file', help='Path to the JSONL log file')
    parser.add_argument('--device-id', default="unknown", help='Device ID for display (default: unknown)')
    
    args = parser.parse_args()
    
    plot_sensor_data(args.log_file, args.device_id)
