package main

import (
	"fmt"
	"net"
	"os"
	"strings"
	"regexp"
	"gopkg.in/yaml.v3"
)

func main() {
	mimirFile := "/etc/mimir.yaml"
	fmt.Print("Mimir file: ", mimirFile, "\n")

	// Fetch the YAML file from MIMIR_YAML environment variable
	var mimir_yaml interface{}
	var err error
	if mimir_yaml, err = envToYaml("MIMIR_YAML"); err != nil{
		fmt.Printf("Error reading variable: %v\n", err)
		os.Exit(1)
	}

	// Replace placeholders recursively
	if mimir_yaml, err = replacePlaceholders(mimir_yaml); err != nil{
		fmt.Printf("Error replacing environment variables: %v\n", err)
		os.Exit(1)
	}

	mimir_str, err := yaml.Marshal(mimir_yaml)
	if err != nil {
		fmt.Printf("Error marshaling YAML: %v\n", err)
		os.Exit(1)
	}

	fmt.Println(string(mimir_str))
	err = os.WriteFile(mimirFile, mimir_str, 0644)
	if err != nil {
		fmt.Printf("Error writing to file: %v\n", err)
		os.Exit(1)
	}

	// Alertmanager
    if os.Getenv("ALERTMANAGER_YML") != ""{
		
		alertManagerFile := "/etc/alertamanager.yaml"
		fmt.Print("Alertmanager file: ", alertManagerFile, "\n")

		var alertManager_yaml interface{}
		if alertManager_yaml, err = envToYaml("ALERTMANAGER_YAML"); err != nil{
			fmt.Printf("Error reading variable: %v\n", err)
			os.Exit(1)
		}

		if alertManager_yaml, err = replacePlaceholders(alertManager_yaml); err != nil{
			fmt.Printf("Error replacing alertmanager environment variables: %v\n", err)
			os.Exit(1)
		}

		alertManagerStr, err := yaml.Marshal(alertManager_yaml)
		if err != nil {
			fmt.Printf("Error marshaling alertmanager YAML: %v\n", err)
			os.Exit(1)
		}

		fmt.Println(string(alertManagerStr))
		err = os.WriteFile(alertManagerFile, alertManagerStr, 0644)
		if err != nil {
			fmt.Printf("Error writing alertmanager file: %v\n", err)
			os.Exit(1)
		}
	}
}


// Fetches a config from an environment variable and parses as an yaml variable
func envToYaml(env_var string) (interface{}, error) {
    yaml_env := os.Getenv(env_var)
    if yaml_env == "" {
        return nil, fmt.Errorf("%s environment variable not set", env_var)
    }

    var yaml_map interface{}
    err := yaml.Unmarshal([]byte(yaml_env), &yaml_map)
    if err != nil {
        return nil, fmt.Errorf("error unmarshalling YAML: %w", err)
    }

    return yaml_map, nil
}

// Replaces placeholders in the YAML data with environment variables
func replacePlaceholders(data interface{}) (interface{}, error) {
	switch v := data.(type) {
	case map[string]interface{}:
		newMap := make(map[string]interface{})
		for key, value := range v {
			newValue, err := replacePlaceholders(value)
			if err != nil {
					return nil, err 
			}
			newMap[key] = newValue
		}
		return newMap, nil
	case []interface{}:
		newSlice := make([]interface{}, len(v))
		for i, item := range v {
			newItem, err := replacePlaceholders(item)
			if err != nil {
				return nil, err
			}
			newSlice[i] = newItem
		}
		return newSlice, nil
	case string:
		re := regexp.MustCompile(`{([A-Za-z0-9_]+)}`) // Matches {ENV_VAR}
		newString := v
		matches := re.FindAllStringSubmatch(v, -1)
		for _, match := range matches {
			if len(match) == 2 { // Ensure we have the full match and capture group
				placeHolder := match[1]
				envVarValue, err := treatPlaceHolder(placeHolder) // Keep the {} for treatPlaceHolder
				if err == nil { // Only replace if the variable is found
					newString = strings.ReplaceAll(newString, match[0], envVarValue)
				} else {
                    return "", fmt.Errorf("error replacing place holder %s: %v", placeHolder, err)
				}
			}
		}
		return newString, nil
	default:
		return v, nil
	}
}

func treatPlaceHolder(placeHolder string) (string, error) {
	switch placeHolder {
	case "MIMIR_YAML":
		return "", fmt.Errorf("cannot use MIMIR_YAML as placeholder")
	case "ALERTMANAGER_YAML":
		return "", fmt.Errorf("cannot use ALERTMANAGER_YAML as placeholder")
	case "ADVERTISE_ADDR_REPLACE":
		interfaceAddr, err := getEth0IP()
		if err != nil {
			return "", fmt.Errorf("error getting interface name: %v", err)
		}
		return interfaceAddr, nil
	default:
		envVar := os.Getenv(placeHolder)
		if envVar == "" {
			return "", fmt.Errorf("environment variable '%s' not found", placeHolder)
		}
		return envVar, nil
	}
}

func getEth0IP() (string, error) {
		interfaces, err := net.Interfaces()
		if err != nil {
			return "", fmt.Errorf("getting interfaces: %w", err)
		}

		for _, iface := range interfaces {
			if iface.Name == "eth0" {
				addrs, err := iface.Addrs()
				if err != nil {
					return "", fmt.Errorf("getting addresses for eth0: %w", err)
				}
				for _, addr := range addrs {
					ipNet, ok := addr.(*net.IPNet)
					if ok && ipNet.IP.To4() != nil { // Ensure it's an IPv4 address
						return ipNet.IP.String(), nil
					}
				}
				return "", fmt.Errorf("no IPv4 address found for eth0")
			}
		}
		return "", fmt.Errorf("interface eth0 not found")
}