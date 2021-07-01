import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

class Transform:
    """
    Transform class for rigid transforms, theta, phi, psi = roll, pitch, yaw
    """

    def __str__(self):
        return str(self.transform)

    def __repr__(self):
        return "Transform({0}, {1}, {2}, {3}, {4}, {5})".format(self.x, self.y, self.z, self.theta, self.phi, self.psi)

    def __init__(self, x=0, y=0, z=0, theta=0, phi=0, psi=0, child=None, parent=None, name=None, transform=None):
        self.child, self.parent, self.name = child, parent, name

        if transform is None:
            # create the transform
            self.transformOnly = False
            self.updateTransform(x, y, z, theta, phi, psi)
        else:
            self.transformOnly = True
            self.transform = transform
            self.xAxis = self.transform[:3, 0]
            self.yAxis = self.transform[:3, 1]
            self.zAxis = self.transform[:3, 2]
            self.origin = self.transform[:3, 3]
    
    # overload multiplication
    def __mul__(self, other):
        result = self.transform @ other.transform
        resultTran = Transform(transform=result)
        # calculate pose from transform
        output = resultTran.inversePose()
        x, y, z, theta, phi, psi = output
        return Transform(x, y, z, theta, phi, psi)
    
    def __eq__(self, other):
        # overload equal sign to work with other transform objects and numpy arrays 
        if isinstance(other, Transform):
            return np.array_equal(self.transform, other.transform)
        elif isinstance(other, np.ndarray):
            return np.array_equal(self.transform, other)

    
    def updateTransform(self, x, y, z, theta, phi, psi):
        """
        updates the transform according to the entered values
        """
        # translation vector
        self.x, self.y, self.z, self.theta, self.phi, self.psi = x, y, z, theta, phi, psi

        self.tran = np.array([
            [1, 0, 0, x], 
            [0, 1, 0, y], 
            [0, 0, 1, z], 
            [0, 0, 0, 1]
        ])

        # roll rotation about x axis
        self.rotX = np.array([
            [1  , 0              , 0              , 0]  ,
            [0  , np.cos(theta)  , -np.sin(theta) , 0]  ,
            [0  , np.sin(theta)  , np.cos(theta)  , 0]  ,
            [0  , 0              , 0              , 1]
        ])

        # pitch rotation about y axis
        self.rotY = np.array([
            [np.cos(phi)   , 0  , np.sin(phi) , 0 ]  ,
            [0             , 1  , 0           , 0 ]  ,
            [-np.sin(phi)  , 0  , np.cos(phi) , 0 ]  ,
            [0             , 0  , 0           , 1]
        ])

        # yaw rotation about z axis
        self.rotZ = np.array([
            [np.cos(psi)  , -np.sin(psi)  , 0  , 0]  ,
            [np.sin(psi)  , np.cos(psi)   , 0  , 0]  ,
            [0            , 0             , 1  , 0]  ,
            [0            , 0             , 0  , 1]
        ])

        self.transform = self.tran @ self.rotZ @ self.rotY @ self.rotX

        # recover the axes for plotting
        self.xAxis = self.transform[:3, 0]
        self.yAxis = self.transform[:3, 1]
        self.zAxis = self.transform[:3, 2]
        self.origin = self.transform[:3, 3]

    def inversePose(self, transform=None):
        """ 
        recovers x,y,z,r,p,y from a given transformation
        """
        if transform is None:
            transform  = self.transform
            
        assert transform.shape == (4, 4), "Wrong size transformation!"

        rot = transform[:3, :3]
        tran = transform[:3, 3]
        x, y, z = tran

        # get yaw
        try:
            psi = np.arctan2(rot[1, 0], rot[0, 0])
            cp = np.cos(psi)
            sp = np.sin(psi)
        except:
            print("Singularity in transform")
            return

        # get pitch
        phi = np.arctan2(-rot[2, 0], rot[0, 0] * cp + rot[1, 0]*sp)
        ct = np.cos(phi)
        st = np.sin(phi)

        theta = np.arctan2(st * (rot[0, 1] * cp + rot[1, 1] * sp) + rot[2, 1] * ct, -rot[0, 1] * sp + rot[1, 1] * cp)

        return x, y, z, theta, phi, psi

    def pose(self):
        """
        return pose associated with the transform
        """
        return np.array([self.x, self.y, self.z, self.theta, self.phi, self.psi]).reshape(-1, 1)

    def plot(self, detached=False, axisObj=None, rgb_xyz=['r', 'g', 'b'], xlim=[-2, 2], ylim=[-2, 2], zlim=[-2, 2], scale_factor=1.0):
        """
        Plots the transform in its parent frame
        """
        if detached:
            return self.__plot_detached(axisObj, rgb_xyz=rgb_xyz, scale_factor=scale_factor)
        else:
            return self.__plot_attached(xlim=xlim, ylim=ylim, zlim=zlim, rgb_xyz=rgb_xyz, scale_factor=scale_factor)

    def __plot_attached(self, xlim, ylim, zlim, rgb_xyz, scale_factor):
        """
        Plots the transform on internally provided matplotlib axes 
        """
        fig = plt.figure()
        axisObj = plt.subplot(111, projection='3d')

        self.__plot_axes(axisObj, rgb_xyz, scale_factor)

        axisObj.set_xlim3d(xlim[0], xlim[1])
        axisObj.set_ylim3d(ylim[0], ylim[1])
        axisObj.set_zlim3d(zlim[0], zlim[1])
        # return true if no errors raised
        plt.show()

    def __plot_detached(self, axisObj, rgb_xyz, scale_factor):
        """
        Plots the transform on externally provided matplotlib axes
        """
        self.__plot_axes(axisObj, rgb_xyz, scale_factor)

    def __plot_axes(self, axisObj, rgb_xyz, scale_factor):
        """ 
        Plots the axes of the transform on a mattplotlib axis
        """
        try:
            # normalize all axes
            xAxis = (scale_factor * self.xAxis ) / np.linalg.norm(self.xAxis) + self.origin
            yAxis = (scale_factor * self.yAxis ) / np.linalg.norm(self.yAxis) + self.origin
            zAxis = (scale_factor * self.zAxis ) / np.linalg.norm(self.zAxis) + self.origin

            # collect plot values
            # i unit vectors
            iX, iY, iZ  = xAxis[0], xAxis[1], xAxis[2]
            # j unit vector
            jX, jY, jZ = yAxis[0], yAxis[1], yAxis[2]
            # k unit vector
            kX, kY, kZ = zAxis[0], zAxis[1], zAxis[2]
            # origin
            oX, oY, oZ = self.origin[0], self.origin[1], self.origin[2]
                    
            axisObj.plot([oX, iX], [oY, iY], [oZ, iZ], rgb_xyz[0])
            axisObj.plot([oX, jX], [oY, jY], [oZ, jZ], rgb_xyz[1])
            axisObj.plot([oX, kX], [oY, kY], [oZ, kZ], rgb_xyz[2])

        except AttributeError:
            raise AttributeError("axisObj is None")

    
    # inverse transform
    def inv(self):
        """
        compute the inverse of the transform
        """
        rot = self.transform[:3, :3]
        tran = self.transform[:3, 3]

        # compute new translation
        x, y, z = -rot.T @ tran

        # initialize new transform as inverse
        return Transform(x, y, z, -self.theta, -self.phi, -self.psi)