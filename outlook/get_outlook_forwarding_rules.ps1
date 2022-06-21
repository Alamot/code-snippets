#Requires -version 2.0
#Author: Alamot
Add-Type -AssemblyName microsoft.office.interop.outlook
$outlook = New-Object -ComObject outlook.application
$namespace = $Outlook.GetNameSpace("mapi")


# See https://docs.microsoft.com/en-us/office/vba/api/outlook.olruleactiontype
$ACTIONS_TO_GRAB = @(6, 7, 8)
# 6 => olRuleActionForward
# 7 => olRuleActionForwardAsAttachment
# 8 => olRuleActionRedirect


[Hashtable[]]$records = $null

ForEach ($store in $namespace.Stores) {

    $records += @{} 
    $records[-1]['CurrentUser'] = $namespace.CurrentUser.Name 
    $records[-1]['DisplayName'] = $store.DisplayName
    $records[-1]['FilePath'] = $store.FilePath
    $records[-1]['Rules'] = $()
    
    $rules = $store.GetRules() 

    ForEach ($rule in $rules) {
        
        if ($rule.Enabled) {

            $actions_to_grab_found = 0
            ForEach ($action in $rule.Actions) {
                if ($action.Enabled -and ($ACTIONS_TO_GRAB -contains $action.ActionType)) {        
                    $actions_to_grab_found = 1
                }
            }

            if ($actions_to_grab_found -eq 1) { 

                $records[-1]['Rules'] += , @{}
                $records[-1]['Rules'][-1]['name'] = $rule.Name  
                $records[-1]['Rules'][-1]['conditions'] = @()
                $records[-1]['Rules'][-1]['actions'] = @()
   
                ForEach ($condition in $rule.Conditions) {
                    if ($condition.Enabled) { 
                        # https://docs.microsoft.com/en-us/office/vba/api/outlook.olruleconditiontype
                        $s = "type:" + $condition.ConditionType.toString()
                        if ("Text" -in $condition.PSobject.Properties.Name) {
                            $s += ", text:" + $condition.Text;
                        }
                        if ("Recipients" -in $condition.PSobject.Properties.Name) {
                            $s += ", recipients:" +
                                 (($condition.Recipients | select -expand Name) -join ';') 
                        }
                        $records[-1]['Rules'][-1]['conditions'] += , $s
                    }
                }

                ForEach ($action in $rule.Actions) {
                    if ($action.Enabled -and ($ACTIONS_TO_GRAB -contains $action.ActionType)) { 
                        $s = "type:" + $action.ActionType.toString() + ", recipients:" + 
                             (($action.Recipients | select -expand Name) -join ';')
                        $records[-1]['Rules'][-1]["actions"] += , $s
                    }
                }   

            }
       
        }
    }
}


$records | ConvertTo-Json -Depth 10 

# Uncomment the following lines and set the proper path to write the output into a file
# $outfile = join-path -path "\\Tcom2\shared" -childpath $($env:COMPUTERNAME + "-" + $(Get-Date -UFormat "%Y-%m-%d") + ".json")
# $records | ConvertTo-Json -Depth 10 | Set-Content $outfile 
