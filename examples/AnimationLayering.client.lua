--[[
	AnimationLayering (LocalScript - put it in StarterCharacterScripts)

	Shows the three things you asked about:
	  1. Sprint / Walk driven by your real movement speed.
	  2. Swinging and blocking WHILE sprinting: the "_UB" (upper body) versions only
	     animate the head + arms, so the legs and torso keep playing Sprint underneath.
	  3. A block that weakens over BLOCK_SECONDS and then breaks, plus the
	     "my attack hit a block" recoil.

	Controls (demo):  Shift = sprint   LMB = swing   F (hold) = block   B = pretend our swing got blocked

	Fill ANIM_IDS after you publish the KeyframeSequences. While testing in Studio
	you can leave them as "" and drop the AnimSaves model into ReplicatedStorage -
	the script registers the KeyframeSequences on the fly (Studio only).
]]

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")

local SIZE = "Medium" -- "Small" | "Medium" | "Large" | "Huge": which object set to use
local BLOCK_SECONDS = 4 -- the block animations are 4 s long; 3-5 s works (we AdjustSpeed)
local WALK_SPEED, SPRINT_SPEED = 16, 26

local ANIM_IDS: { [string]: string } = {
	Walk = "",
	Sprint = "",
	[SIZE .. "Swing"] = "",
	[SIZE .. "Swing_UB"] = "",
	[SIZE .. "SwingBlocked"] = "",
	[SIZE .. "Block"] = "",
	[SIZE .. "Block_UB"] = "",
	[SIZE .. "BlockHit"] = "",
	[SIZE .. "BlockBreak"] = "",
}

local character = script.Parent
local humanoid = character:WaitForChild("Humanoid") :: Humanoid
local animator = humanoid:WaitForChild("Animator") :: Animator
local root = character:WaitForChild("HumanoidRootPart") :: BasePart

local function animationFor(name: string): Animation
	local animation = Instance.new("Animation")
	local id = ANIM_IDS[name]
	if id ~= nil and id ~= "" then
		animation.AnimationId = id
	else
		-- Studio-only fallback: ReplicatedStorage.AnimSaves.<name> (KeyframeSequence)
		local saves = ReplicatedStorage:WaitForChild("AnimSaves")
		animation.AnimationId = KeyframeSequenceProvider:RegisterKeyframeSequence(saves:WaitForChild(name))
	end
	return animation
end

local tracks: { [string]: AnimationTrack } = {}
for name in ANIM_IDS do
	tracks[name] = animator:LoadAnimation(animationFor(name))
end
-- Priorities are already stored in the animations (Walk/Sprint = Movement,
-- swings/blocks = Action2, "got blocked"/break/hit = Action3), so a higher layer
-- always wins for the joints it animates and leaves the other joints alone.

---------------------------------------------------------------------------
-- 1. Locomotion
---------------------------------------------------------------------------
local sprintHeld = false

local function horizontalSpeed(): number
	local v = root.AssemblyLinearVelocity
	return Vector3.new(v.X, 0, v.Z).Magnitude
end

local function isMoving(): boolean
	return horizontalSpeed() > 1
end

RunService.Heartbeat:Connect(function()
	humanoid.WalkSpeed = sprintHeld and SPRINT_SPEED or WALK_SPEED
	local speed = horizontalSpeed()
	local onGround = humanoid.FloorMaterial ~= Enum.Material.Air
	local wantSprint = onGround and speed > WALK_SPEED + 2
	local wantWalk = onGround and speed > 1 and not wantSprint

	for name, want in { Walk = wantWalk, Sprint = wantSprint } do
		local track = tracks[name]
		if want and not track.IsPlaying then
			track:Play(0.15)
		elseif not want and track.IsPlaying then
			track:Stop(0.15)
		end
	end
	-- keep the feet in sync with the ground speed
	if tracks.Walk.IsPlaying then
		tracks.Walk:AdjustSpeed(speed / WALK_SPEED)
	end
	if tracks.Sprint.IsPlaying then
		tracks.Sprint:AdjustSpeed(speed / SPRINT_SPEED)
	end
end)

---------------------------------------------------------------------------
-- 2. Upper-body actions that work while running
---------------------------------------------------------------------------
-- Standing still: use the full-body version (legs step into the hit).
-- Moving: use the _UB version so Sprint/Walk keeps the legs going.
local function actionTrack(baseName: string): AnimationTrack
	local ub = tracks[baseName .. "_UB"]
	if ub and isMoving() then
		return ub
	end
	return tracks[baseName]
end

local currentSwing: AnimationTrack? = nil

local function swing()
	local track = actionTrack(SIZE .. "Swing")
	currentSwing = track
	track:Play(0.05)
end

for _, name in { SIZE .. "Swing", SIZE .. "Swing_UB" } do
	tracks[name]:GetMarkerReachedSignal("Hit"):Connect(function()
		-- do your hitbox check here; play the impact sound
	end)
end

-- Call this when the server tells you the swing landed on someone's block
local function onMySwingBlocked()
	if currentSwing then
		currentSwing:Stop(0.05)
	end
	tracks[SIZE .. "SwingBlocked"]:Play(0.03)
end

---------------------------------------------------------------------------
-- 3. Block that weakens, then breaks
---------------------------------------------------------------------------
local blockTrack: AnimationTrack? = nil

local function startBlock()
	blockTrack = actionTrack(SIZE .. "Block")
	local track = blockTrack :: AnimationTrack
	track:Play(0.1)
	track:AdjustSpeed(4 / BLOCK_SECONDS) -- 4 s of animation squeezed/stretched to BLOCK_SECONDS
end

local function stopBlock()
	if blockTrack then
		blockTrack:Stop(0.15)
		blockTrack = nil
	end
end

local function breakBlock()
	stopBlock()
	tracks[SIZE .. "BlockBreak"]:Play(0.05)
end

for _, name in { SIZE .. "Block", SIZE .. "Block_UB" } do
	tracks[name]:GetMarkerReachedSignal("Exhausted"):Connect(breakBlock)
end

-- Call this when an attack hits our block (e.g. from a RemoteEvent)
local function onBlockStruck()
	if blockTrack then
		tracks[SIZE .. "BlockHit"]:Play(0.03)
	end
end

---------------------------------------------------------------------------
-- Demo input
---------------------------------------------------------------------------
UserInputService.InputBegan:Connect(function(input, processed)
	if processed then
		return
	end
	if input.KeyCode == Enum.KeyCode.LeftShift then
		sprintHeld = true
	elseif input.UserInputType == Enum.UserInputType.MouseButton1 then
		swing()
	elseif input.KeyCode == Enum.KeyCode.F then
		startBlock()
	elseif input.KeyCode == Enum.KeyCode.B then
		onMySwingBlocked()
	elseif input.KeyCode == Enum.KeyCode.G then
		onBlockStruck()
	end
end)

UserInputService.InputEnded:Connect(function(input)
	if input.KeyCode == Enum.KeyCode.LeftShift then
		sprintHeld = false
	elseif input.KeyCode == Enum.KeyCode.F then
		stopBlock()
	end
end)
