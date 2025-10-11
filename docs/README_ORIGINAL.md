# Loggrep

**Loggrep** is a powerful command-line tool for searching log files, designed to work with timestamps and support advanced features like regex, invert match, context lines, and color output. It’s inspired by `grep` but tailored for log files, allowing you to search only after a specific startup time.

This last item is the crucial feature - you want to look at log files, e.g. on android after startup - you start up the app on your phone and you get a pile of lines that are irrelevant that happened in the past... who cares - that's where loggrep comes in - it filters out all the old stuff.

ps. this was vibe coded - it works for me - if you spot any issues just submit a pull request or a bug.

---

## **Features**
- **Timestamp-aware searching**: Only search log lines after a specified startup time.
- **Regex support**: Use full regex patterns for powerful matching.
- **Invert match (`-v`)**: Show lines that do **not** match the pattern.
- **Context lines (`-A`, `-B`, `-C`)**: Show lines before, after, or around matches.
- **Color output**: Highlight matches for better readability.
- **Multiple patterns**: Search for multiple patterns at once.
- **Flexible timestamp parsing**: Supports Unix syslog, Android logcat, and other common log formats.
- **Stdin/file input**: Read from stdin or a file.

---

## **Installation**

### **Prerequisites**
- Python 3.6+
- `pip` for installing dependencies

### **Install Dependencies**
```bash
pip install python-dateutil colorama
```

### Install Loggrep

1. Clone this repository:

```bash
git clone https://github.com/yourusername/loggrep.git
cd loggrep
```

2. Make the script executable:

```bash
chmod +x loggrep.py
```

3. (Optional Install globally:

```bash
sudo ln -s \$(pwd)/loggrep.py" /usr/local/bin/loggrep
```

## Usage

```bash
loggrep.py <pattern> [--file LOG_FILE] [--startup-time STARTUP_TIME] [OPTIONS]
```

## Arguments

| Argument | Description |
|-|--|-|
| pattern | Regex pattern(s) to search for. Multiple patterns are OR'd together. |
| --file | Path to the log file. If not provided, reads from stdin. |
| --startup-time | Startup time (e.g., "2025-10-04 12:00:00"). Uses the first timestamp if omitted. |

## Options

| Option | Description |
|-|--|-|
| -i, --ignore-case | Ignore case in regex matching. |
| -v, --invert-match | Invert match (show non-matching lines). |
| -A NUM | Show NUM lines after match. |
| -B NUM | Show NUM lines before match. |
| -C NUM | Show NUM lines around match. |
| --color | Control color output: always, never, or auto (default). |

## Examples

### Basic Usage

Search for "ERROR" in /var/log/syslog

```bash
sudo ./loggrep.py "ERROR" --file /var/log/syslog
```

### Case-Insensitive Search

```bash
sudo ./loggrep.py -i "error" --file /var/log/syslog
```

### Invert Match

Show lines that do *not* contain "OK":

```bash
sudo ./loggrep.py -v "OK" --file /var/log/syslog
```

### Context Lines

Show 2 lines before and after each match:

```bash
sudo ./loggrep.py "ERROR" --file /var/log/syslog -C 2
```

### Multiple Patterns

Search for "ERROR" or "WARN":

```bash
sudo ./loggrep.py "ERROR" "WARN" --file /var/log/syslog
```

### Read from Stdin

```bash
sudo cat /var/log/syslog | ./loggrep.py "ERROR"
```

### Color Output

Force color output:

```bash
sudo ./loggrep.py "ERROR" --file /var/log/syslog --color=always
```

### Supported Timestamp Formats
Loggrep automatically detects and parses common timestamp formats, including:

* Unix syslog: Oct  5 00:00:02
* Android logcat: 10-05 00:00:00.123
* ISO 8601: 2025-10-05 00:00:02.123
* Custom formats: Add more regex patterns to detect_timestamp_format() if needed.

## License
This project is licensed under the Apache-2.0 License. See LICENSE for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## Acknowledgments

* Inspired by grep and tailored for log files.
* Uses python-dateutil for flexible timestamp parsing.
* Uses colorama for cross-platform color output.




